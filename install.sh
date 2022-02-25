#! /bin/sh

# 该脚本会依次安装并打包所有的依赖库

# 安装基础库 template_exception template_transaction
current_pwd=$(pwd)
dist_path="$current_pwd/dist"
egg_path="$current_pwd/egg"
# 创建目标目录
rm -rf "$dist_path"
rm -rf "$egg_path"
mkdir -p "$dist_path"
mkdir -p "$egg_path"

# 遍历libs目录进行安装
for file in "$current_pwd"/libs/*
do
    if test -d "$file"
    then
        cd "$file" || exit
        echo "准备打包依赖库......$file"
        python3 setup.py sdist -d "$dist_path/" egg_info --egg-base "$egg_path/"
        echo "完成打包依赖库......$file"
    fi
done

# 清理构建产生的中间文件
echo "清理egg_path"
rm -rf "$egg_path"

# 升级pip
pip install --upgrade pip
# 安装依赖
pip3 install "$dist_path"/*
