#!/bin/sh

cat > /etc/systemd/system/swarm-manager.service << END_SERVICE_TOP
[Unit]
Description=Swarm Manager
After=docker.service
Requires=docker.service

[Service]
TimeoutStartSec=0
ExecStartPre=-/usr/bin/docker kill swarm-manager
ExecStartPre=-/usr/bin/docker rm swarm-manager
ExecStartPre=/usr/bin/docker pull swarm:0.2.0
#TODO: roll-back from swarm:0.2.0 to swarm if atomic image can work with latest swarm image
ExecStart=/usr/bin/docker run --name swarm-manager \\
                              -v /etc/docker:/etc/docker \\
                              -p 2376:2375 \\
                              -e http_proxy=$HTTP_PROXY \\
                              -e https_proxy=$HTTPS_PROXY \\
                              -e no_proxy=$NO_PROXY \\
                              swarm:0.2.0 \\
                              manage -H tcp://0.0.0.0:2375 \\
END_SERVICE_TOP

if [ $INSECURE = 'False'  ]; then

cat >> /etc/systemd/system/swarm-manager.service << END_TLS
                                  --tls \\
                                  --tlsverify \\
                                  --tlscacert=/etc/docker/ca.crt \\
                                  --tlskey=/etc/docker/server.key \\
                                  --tlscert=/etc/docker/server.crt \\
END_TLS

fi

cat >> /etc/systemd/system/swarm-manager.service << END_SERVICE_BOTTOM
                                  $DISCOVERY_URL
ExecStop=/usr/bin/docker stop swarm-manager
ExecStartPost=/usr/bin/curl -sf -X PUT -H 'Content-Type: application/json' \\
  --data-binary '{"Status": "SUCCESS", "Reason": "Setup complete", "Data": "OK", "UniqueId": "00000"}' \\
  "$WAIT_HANDLE"

[Install]
WantedBy=multi-user.target
END_SERVICE_BOTTOM

chown root:root /etc/systemd/system/swarm-manager.service
chmod 644 /etc/systemd/system/swarm-manager.service
