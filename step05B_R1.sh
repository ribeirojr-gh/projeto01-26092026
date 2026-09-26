rm -rf /tmp/upb_step05B_R1
mkdir -p /tmp/upb_step05B_R1

unzip -q \
packages/petrobras_upb_step05B_R1_memory_safe.zip \
-d /tmp/upb_step05B_R1

cp -a \
/tmp/upb_step05B_R1/petrobras_upb_project/. \
.

bash step05B_pbca_size_gate/run-step05B.sh
