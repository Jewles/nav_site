#!/usr/bin/env python3
"""IT 导航站 - 轻量书签管理 (MySQL)"""

import os
import glob
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify, send_from_directory
import pymysql

app = Flask(__name__)
app.secret_key = os.urandom(24)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLPAPER_DIR = os.path.join(BASE_DIR, 'static', 'wallpapers')
os.makedirs(WALLPAPER_DIR, exist_ok=True)
ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}

def get_current_wallpaper():
    """返回最新上传的壁纸文件名，没有则 None"""
    files = []
    for ext in ALLOWED_EXT:
        files.extend(glob.glob(os.path.join(WALLPAPER_DIR, '*' + ext)))
    if not files:
        return None
    return os.path.basename(max(files, key=os.path.getmtime))

# ── MySQL 配置 ──────────────────────────────────────
DB_CONFIG = {
    'host': os.environ.get('NAV_DB_HOST', 'youer_ip'),
    'port': int(os.environ.get('NAV_DB_PORT', 3306)),
    'user': os.environ.get('NAV_DB_USER', 'sql_user'),
    'password': os.environ.get('NAV_DB_PASS', 'your_pwd'),
    'database': os.environ.get('NAV_DB_NAME', 'sql_name'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

DB_NAME = DB_CONFIG['database']


# ── 数据库 ──────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


def init_db():
    """创建库和表（幂等）"""
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARSET utf8mb4")
        cur.execute(f"USE `{DB_NAME}`")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id   INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(64) NOT NULL UNIQUE,
                sort INT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id      INT AUTO_INCREMENT PRIMARY KEY,
                cat_id  INT NOT NULL,
                name    VARCHAR(128) NOT NULL,
                url     VARCHAR(512) NOT NULL,
                `desc`  VARCHAR(256) DEFAULT '',
                sort    INT DEFAULT 0,
                FOREIGN KEY (cat_id) REFERENCES categories(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # 预置分类
        cur.execute("SELECT COUNT(*) AS cnt FROM categories")
        if cur.fetchone()['cnt'] == 0:
            cats = [
                ('监控平台', 1), ('CI/CD', 2), ('云服务', 3),
                ('运维工具', 4), ('文档/Wiki', 5),
            ]
            cur.executemany(
                "INSERT INTO categories (name, sort) VALUES (%s, %s)", cats
            )
        conn.commit()
    conn.close()


# ── 首页 ──────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    with db.cursor() as cur:
        cur.execute('SELECT * FROM categories ORDER BY sort, id')
        cats = cur.fetchall()
    data = []
    for cat in cats:
        with db.cursor() as cur:
            cur.execute(
                'SELECT * FROM links WHERE cat_id = %s ORDER BY sort, id',
                (cat['id'],)
            )
            links = cur.fetchall()
        data.append({'cat': cat, 'links': links})
    return render_template('index.html', data=data)


# ── 管理页 ────────────────────────────────────────────
@app.route('/admin')
def admin():
    db = get_db()
    with db.cursor() as cur:
        cur.execute('SELECT * FROM categories ORDER BY sort, id')
        cats = cur.fetchall()
        cur.execute('''
            SELECT l.*, c.name AS cat_name
            FROM links l JOIN categories c ON l.cat_id = c.id
            ORDER BY l.cat_id, l.sort, l.id
        ''')
        links = cur.fetchall()
    return render_template('admin.html', cats=cats, links=links)


# ── 重排分类顺序 ──────────────────────────────────────
@app.route('/cat/reorder', methods=['POST'])
def cat_reorder():
    ids = request.json.get('ids', [])
    db = get_db()
    with db.cursor() as cur:
        for i, cat_id in enumerate(ids):
            cur.execute('UPDATE categories SET sort=%s WHERE id=%s', (i, int(cat_id)))
    db.commit()
    return jsonify({'ok': True})


# ── 添加分类 ──────────────────────────────────────────
@app.route('/cat/add', methods=['POST'])
def cat_add():
    name = request.form['name'].strip()
    if not name:
        flash('分类名不能为空')
        return redirect(url_for('admin'))
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute('INSERT INTO categories (name) VALUES (%s)', (name,))
        db.commit()
    except Exception:
        flash('分类已存在')
    return redirect(url_for('admin'))


# ── 删除分类 ──────────────────────────────────────────
@app.route('/cat/<int:cat_id>/delete', methods=['POST'])
def cat_delete(cat_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute('DELETE FROM categories WHERE id = %s', (cat_id,))
    db.commit()
    return redirect(url_for('admin'))


# ── 添加链接 ──────────────────────────────────────────
@app.route('/link/add', methods=['POST'])
def link_add():
    cat_id = request.form['cat_id']
    name = request.form['name'].strip()
    url_val = request.form['url'].strip()
    desc = request.form.get('desc', '').strip()

    if not name or not url_val:
        flash('名称和 URL 必填')
        return redirect(url_for('admin'))

    if url_val and not url_val.startswith(('http://', 'https://')):
        url_val = 'https://' + url_val

    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            'INSERT INTO links (cat_id, name, url, `desc`) VALUES (%s, %s, %s, %s)',
            (cat_id, name, url_val, desc)
        )
    db.commit()
    return redirect(url_for('admin'))


# ── 编辑链接 ──────────────────────────────────────────
@app.route('/link/<int:link_id>/edit', methods=['POST'])
def link_edit(link_id):
    cat_id = request.form['cat_id']
    name = request.form['name'].strip()
    url_val = request.form['url'].strip()
    desc = request.form.get('desc', '').strip()

    if not name or not url_val:
        flash('名称和 URL 必填')
        return redirect(url_for('admin'))

    if url_val and not url_val.startswith(('http://', 'https://')):
        url_val = 'https://' + url_val

    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            'UPDATE links SET cat_id=%s, name=%s, url=%s, `desc`=%s WHERE id=%s',
            (cat_id, name, url_val, desc, link_id)
        )
    db.commit()
    return redirect(url_for('admin'))


# ── 删除链接 ──────────────────────────────────────────
@app.route('/link/<int:link_id>/delete', methods=['POST'])
def link_delete(link_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute('DELETE FROM links WHERE id = %s', (link_id,))
    db.commit()
    return redirect(url_for('admin'))


# ── 获取当前壁纸（注入所有模板） ───────────────────
@app.context_processor
def inject_wallpaper():
    return {'wallpaper': get_current_wallpaper()}


# ── 壁纸上传 ────────────────────────────────────────
@app.route('/wallpaper/upload', methods=['POST'])
def wallpaper_upload():
    if 'file' not in request.files:
        flash('请选择图片文件')
        return redirect(url_for('admin'))
    f = request.files['file']
    if not f.filename:
        flash('未选择文件')
        return redirect(url_for('admin'))
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        flash(f'不支持的格式 {ext}，仅支持 PNG / JPG / WebP / GIF')
        return redirect(url_for('admin'))
    name = uuid.uuid4().hex + ext
    f.save(os.path.join(WALLPAPER_DIR, name))
    return redirect(url_for('admin'))


# ── 移除壁纸 ────────────────────────────────────────
@app.route('/wallpaper/remove', methods=['POST'])
def wallpaper_remove():
    """删除所有壁纸"""
    for ext in ALLOWED_EXT:
        for fp in glob.glob(os.path.join(WALLPAPER_DIR, '*' + ext)):
            os.remove(fp)
    return redirect(url_for('admin'))


# ── 壁纸静态文件服务 ────────────────────────────────
@app.route('/wallpapers/<filename>')
def wallpaper_file(filename):
    return send_from_directory(WALLPAPER_DIR, filename)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5800, debug=True)
