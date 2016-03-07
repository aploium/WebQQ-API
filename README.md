# WebQQ_API `v1.09.01`
利用WebQQ的API来发送和接受信息  
并且提供了一个服务器,允许其他程序/计算机方便地通过本机来发送QQ消息,支持http  
各种API功能介绍请看webqq_api.py中的说明
  
# 运行需求
 - Python 3.4+
 - firefox(仅在首次运行,获取session时需要,二次运行时不需要firefox)
 - selenium(一个python模块,已内置)
 - requests(一个python模块,已内置)

# 安装
 - 从[Python官网](https://www.python.org/downloads/release)下载Python3并安装
 - 若你有git `git clone https://github.com/Aploium/WebQQ_API.git`
 - 若你没有git 点[这里](https://github.com/Aploium/WebQQ_API/archive/master.zip)下载程序压缩包

# 参数
 
    -h --help: 显示本帮助  
    -m (MasterQQ) --master-qq: [必须]指定大号QQ(不是登陆的QQ,登陆用账号需要是小号),当verbose=4时大号QQ有执行任意python命令的权限  
    -d (masterDiscuss) --master-discuss: (可选)在webqq服务器出问题的这段时间(截止2016.03.07尚未恢复),指定接收信息的讨论组  
    -v (0-4)  --verbose: verbose level 默认3  
    -n  --new-session: 清理session并重新登陆(session被保存在脚本文件夹的session.dat中,有效期大约3天)  
  
    -s  --start-server: 启动webqq消息服务器,供外部程序/计算机通过本机发送消息到qq(基本必用的一个选项,使用方法见同文件夹 的webqq_client.py)  
    -t (token) --token: (可选,建议指定)webqq消息服务器的token,其余程序/计算机必须给出正确的token才能发送消息,默认为 apl,使用多个-t指定多个可用token  
    -p (port) --port: (可选,不建议修改)webqq消息服务器的端口,默认为34567  
    
  example: python main.py -m 333333333 -d "qwertyuiop" -s -v 4 -t "just_a_token" -t "another_token"  
    在上例中,会打开firefox让你手动登陆(再次提醒,请登陆小号),大号qq为333333333,大号讨论组为qwertyuiop,启动webQQ消息服务器,服务器token为just_a_token与another_token  

# 服务器启动后的信息发送
  若为首次使用,请运行`python3 webqq_client.py`来运行消息发送的demo  
  
  若需要在自己的程序中加入发送QQ信息的功能,请查看webqq_client.py顶部的介绍  
  
