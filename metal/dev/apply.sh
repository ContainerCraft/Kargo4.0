#!/bin/bash -x
#talosctl gen secrets
#talosctl gen config dev https://192.168.1.60:6443/ \
#--install-image "factory.talos.dev/installer/b027a2d9dddfa5c0752c249cf3194bb5c62294dc7cba591f3bec8119ab578aea:v1.7.4" \
#--output-types controlplane,worker,talosconfig \
#--with-secrets secrets.yaml \
#--config-patch @template.yaml \
#--install-disk "/dev/vda" \
#--output ./ \
#--persist \
#--force

kubectl delete -f kubevirt.vm.yaml --wait=true ; sleep 1 ; kubectl delete -f kubevirt.vm.yaml --wait=true ; sleep 3
kubectl delete secret talos-userdata-cp1 ; sleep 1

kubectl create secret generic talos-userdata-cp1 --dry-run=client --output=yaml \
--from-file=userdata=controlplane.yaml \
| kubectl apply -f -


kubectl apply -f kubevirt.vm.yaml || kubectl apply -f kubevirt.vm.yaml
