import os
from flask import Flask, request, g, redirect, url_for, render_template, flash
import models
from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import time
import io
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sklearn import decomposition
from sklearn.cluster import KMeans

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = './static/csv_data/'
app.config['DEBUG'] = True
# app.config.from_json({
#     "SQLALCHEMY_DATABASE_URI": "sqlite:///test.db",
#     "SECRET_KEY": "hogehoge",
#     "UPLOAD_FOLDER": "/static/csv_data",
# })

ALLOWED_EXTENSIONS = set(["csv"])

db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    data = db.Column(db.Text(), unique=False, nullable=False)
    img = db.Column(db.Text(), unique=True, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    def __repr__(self):
        return '<Post %r>' % self.title


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 以下、画面に関わるメソッド
@app.route('/')
def index():
    """ 一覧画面 """
    posts = Post.query.all()
    return render_template('index.html', posts=posts)
 
 
@app.route('/create')
def create():
    """ 新規作成画面 """
    return render_template('edit.html')
 
 
@app.route('/analysis', methods=['POST'])
def analysis():
    """ 分析実行処理 """
    title = request.form['title']
    label = request.form['pca_label']
    print(request.form)
    res = request.form
    
    if request.form["upload_data"] == "text":
        data = request.form['text_data']
        df = data.replace(',', '\t').replace(' ', '\t')
        df = pd.read_csv(io.StringIO(df), sep='\t')
        print(data)
    else:
        print(request.url)
        data = request.files['file_data']
        print(data)
        filename = time.strftime('%Y%m%d%H%M%S') + ".csv"
        data.save(app.config['UPLOAD_FOLDER'] + filename)
        with open(app.config['UPLOAD_FOLDER'] + filename, 'r') as f:
            print(f)
            df = pd.read_csv(f)
            data = f.read()
            print(data)
        if 'upload_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

    img = create_plot(df, res)
    post = Post(title=title, data=data, img=img)
    db.session.add(post)
    db.session.commit()
    pk = post.id
    flash('登録処理が完了しました。')
    return redirect(url_for('view', pk=pk))
 
 
@app.route('/delete/<pk>', methods=['POST'])
def delete(pk):
    """ 結果削除処理 """
    de = Post.query.filter_by(id=pk).first()
    db.session.delete(de)
    db.session.commit()
    flash('削除処理が完了しました。')
    return redirect(url_for('index'))
 
 
@app.route('/view/<pk>')
def view(pk):
    """ 結果参照処理 """
    result = Post.query.filter_by(id=pk).first()
    return render_template('view.html', result=result)

def create_plot(data, res):
    if res["method"] == "pca":
        print(res["pca_label"])
        pca = decomposition.PCA(n_components=2)
        # pca.fit(data.drop(res["pca_label"], axis=1))
        label = data[res["pca_label"]]
        X_transformed = pca.fit_transform(data.drop(res["pca_label"], axis=1))
        plt.scatter(X_transformed[:,0],X_transformed[:,1], c=label.values)
    if res["method"] == "scatter":
        if len(data.columns) == 2:
            sns.jointplot(data.columns[0], data.columns[1], data=data, kind="reg")
        else:
            if bool(res["pca_label"]) == True:
                sns.pairplot(data, hue=res["pca_label"])
            else:
                sns.pairplot(data)
    if res["method"] == "boxplot":
        sns.boxplot(x="column", y="data", data=data.sort('size'))
    if res["method"] == "distribution":
        sns.stripplot(x="column", y="data", data=tips)
    if res["method"] == "k_means":
        k_means = KMeans(n_clusters=int(res["num_cluster"]))
        k_means.fit(data)
        label = k_means.labels_
        pca = decomposition.PCA(n_components=2)
        X_transformed = pca.fit_transform(data)
        plt.scatter(X_transformed[:,0],X_transformed[:,1], c=label)

    filename = time.strftime('%Y%m%d%H%M%S') + ".png"
    save_path = "./static/result/" + filename
    # 表示用URL
    url = "result/" + filename
    plt.savefig(save_path)
    plt.close()
    return url

def plot_pca(data):
    pass


if __name__ == '__main__':
    app.run()