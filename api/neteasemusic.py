"""
Module/Script Name: NetEaseMusic Data API
Author: RyanZhang
Date: 1/12/2023

Description: 网易云音乐接口
Interface_List:

Dependencies:
- sqlalchemy
- pandas

"""
import json
import math
import os
import uuid

import pandas as pd

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, FileResponse

from dependent import mysql
from models.neteasemusic import NetEaseMusic
from utils.serialized import encode_custom

router = APIRouter()


def get_db():
    db = mysql.connectSql()
    try:
        yield db
    finally:
        db.close()


@router.get("/music")
def get_video(page: int = 0, num: int = 100, db: Session = Depends(get_db)):
    start = page * num
    if page == 1:
        start = 0
    data = db.query(NetEaseMusic).offset(start).limit(num).all()
    count = db.query(NetEaseMusic).count()
    # 反序列化
    serialized_data = json.dumps(data, default=encode_custom)
    return JSONResponse(content={"code": 0,
                                 "message": "success",
                                 "page": page if page != 0 else page + 1,  # 当前页数
                                 "number": num,  # 单页显示数量
                                 "count": math.ceil(count / num),  # 总页数
                                 "sum": count,  # 数据总量
                                 "data": json.loads(serialized_data)})  # 数据


@router.get("/download_data")
def download_data(db: Session = Depends(get_db)):
    fileName = str(uuid.uuid4()) + ".csv"
    filePath = os.path.join(os.getcwd(), "tmp_file", fileName)
    # 执行SQL查询
    query_result = db.query(NetEaseMusic).all()
    # 获取列名
    columns = query_result[0].__table__.columns.keys() if query_result else []
    # 将数据转为 Pandas DataFrame
    df = pd.DataFrame([{col: getattr(item, col) for col in columns} for item in query_result])
    # 将 DataFrame 保存为 CSV 文件
    df.to_csv(filePath, index=False)
    # 设置响应头，告诉浏览器文件类型和文件名
    response = FileResponse(filePath, filename=fileName,
                            media_type="text/csv")
    return response
