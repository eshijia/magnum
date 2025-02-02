#!/bin/sh

. /etc/sysconfig/heat-params

echo "configuring kubernetes (minion)"

myip=$(ip addr show eth0 |
awk '$1 == "inet" {print $2}' | cut -f1 -d/)
myip_last_octet=${myip##*.}

ETCD_SERVER_IP=${ETCD_SERVER_IP:-$KUBE_MASTER_IP}

sed -i '
/^KUBE_ALLOW_PRIV=/ s/=.*/="--allow_privileged='"$KUBE_ALLOW_PRIV"'"/
/^KUBE_ETCD_SERVERS=/ s|=.*|="--etcd_servers=http://'"$ETCD_SERVER_IP"':2379"|
/^KUBE_MASTER=/ s|=.*|="--master=http://'"$KUBE_MASTER_IP"':8080"|
' /etc/kubernetes/config

sed -i '
/^KUBELET_ADDRESS=/ s/=.*/="--address=0.0.0.0"/
/^KUBELET_HOSTNAME=/ s/=.*/="--hostname_override='"$myip"'"/
/^KUBELET_API_SERVER=/ s|=.*|="--api_servers=http://'"$KUBE_MASTER_IP"':8080"|

' /etc/kubernetes/kubelet

sed -i '
/^KUBE_MASTER=/ s/=.*/="--master='"$KUBE_MASTER_IP"':8080"/
' /etc/kubernetes/apiserver

if [ "$NETWORK_DRIVER" == "flannel" ]; then
sed -i '
/^FLANNEL_ETCD=/ s|=.*|="http://'"$ETCD_SERVER_IP"':2379"|
' /etc/sysconfig/flanneld
fi

cat >> /etc/environment <<EOF
KUBERNETES_MASTER=http://$KUBE_MASTER_IP:8080
EOF

sed -i '/^DOCKER_STORAGE_OPTIONS=/ s/=.*/=--storage-driver devicemapper --storage-opt dm.fs=xfs --storage-opt dm.thinpooldev=\/dev\/mapper\/docker-docker--pool --storage-opt dm.use_deferred_removal=true/' /etc/sysconfig/docker-storage

systemctl enable kube-register

