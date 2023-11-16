# AutoXHS 管理终端

## 打包方式

拉取源码后，配置解释器，建议虚拟环境

执行下述命令安装第三方依赖：

```bash
pip install -r requirements.txt

pip install pyinstaller
```

暂时只支持 windows 平台，其他系统的朋友请自行打包

> 先修改 config.py 中的代码，分别是数据库配置与接口地址

接下来直接双击 setup.bat 即可打包