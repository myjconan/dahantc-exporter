apt-get update
#jenkins pipeline必备库
apt-get install -y jq
#vim编辑器
apt-get install -y vim
#网络测试库
apt-get install -y inetutils-ping
apt-get install -y telnet
apt-get install -y dnsutils
apt-get install -y iproute2
apt-get install -y iptables
#k8s相关
apt-get install -y apt-transport-https
curl https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | apt-key add -
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main
EOF
apt-get install -y kubectl
#apt-get install -y kubelet
pip install kubernetes
pip install pandas
pip install prometheus_client
# pip install tornado
pip install dmPython
pip install pymysql
pip install flask
# #ssh
# apt-get install -y openssh-server
# echo -e "PermitRootLogin yes\nPasswordAuthentication yes" >>/etc/ssh/sshd_config
# # 修改密码
# echo -e "123456\n123456\n" | passwd root
