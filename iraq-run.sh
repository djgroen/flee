#python3 iraq-idp.py 1500 > outiraq/out.csv &
#wait
#rm outiraq/*.png
python3 plot-flee-output.py outiraq > outiraq/error.txt

mkdir -p outiraq/rescaled
mv outiraq/*rescaled*png outiraq/rescaled
wait
