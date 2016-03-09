# WebQQ_API `v1.09.01`
利用WebQQ的API来发送和接受QQ信息  
并且内置了一个服务端程序,允许其他程序/计算机方便地通过本机来发送QQ消息,支持http  
若需要二次开发,封装的各种API功能介绍请看webqq_api.py中的说明,API提取自webQQ网站中的js
  
## 运行需求
 - 服务端主程序main.py: Python 3.4+  
 - 客户端模块webqq_client.py: Python 2.6+/3.x  
   - 客户端若使用http则无python要求
 - firefox (仅在服务器首次运行,获取session时需要,服务端二次运行/客户端不需要firefox)
 - selenium (一个python模块,已内置)
 - requests (一个python模块,已内置)

## 安装
 - 1.从[Python官网](https://www.python.org/downloads/release)下载Python3并安装
 - 2.若你有git `git clone https://github.com/Aploium/WebQQ_API.git`
 - 2.若你没有git 点[这里](https://github.com/Aploium/WebQQ_API/archive/master.zip)下载程序压缩包

## 参数
 
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

## 运行指南
  0. 安装  
  1. 请准备一个QQ小号(淘宝上能买到),并与大号互加好友  
  2. (可选,但是建议)新建一个与大号的二人讨论组(多人也允许),讨论组名字取得独特一点,比如`F3gbX5Op`,程序根据讨论组名字识别讨论组  
    (因为近期(2016.03.09)WebQQ服务器大姨妈,QQ私聊功能出问题,偶尔信息会发不出去,讨论组还是完好的)  
  3. `python3 main.py -m 你大号的QQ号 -s -t 你随便自定义的一个token [-d 二人讨论组的名字,若没有则忽略此参数]`  
  4. 运行上述命令后会弹出一个firefox窗口,请在窗口中登陆自己的__QQ小号__,此后不再需要手工操作  
  5. 程序会访问几个qq站点(比如www.qq.com,这是为了获取domain限制的cookies),请稍等  
  6. 完成后firefox会自动关闭,在脚本所在目录生成一个`session.dat`,下次启动时会读取文件中的信息,不再需要启动firefox登陆(除非指定`-n`参数来重置session),此后服务端会等待客户端的输入,并不断获取发送给小号的QQ信息 _暂时无法自动检测session的失效,失效周期大约是3天_  
  7. 若为首次使用,请运行`python3 webqq_client.py`或`python2 webqq_client.py`来运行消息发送的demo  
  8. 如果一切正常,将会有一条消息发送到你的QQ/讨论组上  
  
## 外部程序的调用
  - 若为python程序(2.x/3.x): `webqq_client.py`可作为模块直接导入(只需要这么一个文件)
    ```python
    from webqq_client import WebqqClient
    # 服务端需要已经运行main.py,并且防火墙开放端口34567(默认)
    server = '127.0.0.1'
    target = 'JustADemoDiscussGroup'
    token = 'your_self_defined_token'
    port = None  # 默认端口是34567,int类型
    target_type = 'discuss'  # 'qq'->QQ朋友 'discuss'->讨论组 暂不支持群

    q_client = WebqqClient(
        server,  # 服务器地址
        token=token,  # 前面你自定义的token
        target=target,  # 默认的目标(一般就是你自己)
        default_target_type=target_type,  # 默认目标的类型,即上一行target的类型 'qq'->QQ朋友 'discuss'->讨论组
        port=port  # 端口,一般不需要指定,使用默认值即可
    )
    # ps:支持中文
    q_client.send('hello world!_default')  # 会发送到上面的默认目标
    q_client.send_to_qq('hello world!_qq', target_qq='345678901')  # 发送到QQ(必须是好友)
    q_client.send_to_discuss('hello world!_disciss', target_discuss_name='JustAnotherDisscussName')  # 发送到讨论组(必须是成员)
    ```
  
  - 若不是python程序: 服务器支持http协议,任何能发送http请求的程序都能调用  
    - 这部分比较长,请打开`webqq_client.py`,看文件头部的介绍)  
  
