#!/bin/bash

rm tmp.txt

for i in 150 175 200 225 250
do

  echo $i >> tmp.txt
  for j in "outbur" "outcar" "out300"
  do
    cat sensitivity-campweight${i}/error.txt | grep "error" | grep "${j}" | awk '{print $6}' >> tmp.txt
  done
  for j in "outbur" "outcar" "out300"
  do
    cat sensitivity-campweight${i}/error.txt | grep "error" | grep "${j}" | awk '{print $9}' >> tmp.txt
  done
done

echo "#campweight,bur-normal,car-normal,mali-normal,bur-rescaled,car-rescaled,mali-rescaled"
sed 'N;N;N;N;N;N;s/\n/,/g' tmp.txt


rm tmp.txt

for i in 15 20 25 30 35
do

  echo $i >> tmp.txt
  for j in "outbur" "outcar" "out300"
  do
    cat sensitivity-conflictweight0${i}/error.txt | grep "error" | grep "${j}" | awk '{print $6}' >> tmp.txt
  done
  for j in "outbur" "outcar" "out300"
  do
    cat sensitivity-conflictweight0${i}/error.txt | grep "error" | grep "${j}" | awk '{print $9}' >> tmp.txt
  done
done

echo "#conflictweight,bur-normal,car-normal,mali-normal,bur-rescaled,car-rescaled,mali-rescaled"
sed 'N;N;N;N;N;N;s/\n/,/g' tmp.txt


rm tmp.txt

for i in 080 085 090 095 100
do

  echo $i >> tmp.txt
  for j in "outbur" "outcar" "out300"
  do
    cat sensitivity-conflictmovechance${i}/error.txt | grep "error" | grep "${j}" | awk '{print $6}' >> tmp.txt
  done
  for j in "outbur" "outcar" "out300"
  do
    cat sensitivity-conflictmovechance${i}/error.txt | grep "error" | grep "${j}" | awk '{print $9}' >> tmp.txt
  done
done

echo "#conflictmovechance,bur-normal,car-normal,mali-normal,bur-rescaled,car-rescaled,mali-rescaled"
sed 'N;N;N;N;N;N;s/\n/,/g' tmp.txt


rm tmp.txt

for i in 020 025 030 035 040
do

  echo $i >> tmp.txt
  for j in "outbur" "outcar" "out300"
  do
    cat sensitivity-defaultmovechance${i}/error.txt | grep "error" | grep "${j}" | awk '{print $6}' >> tmp.txt
  done
  for j in "outbur" "outcar" "out300"
  do
    cat sensitivity-defaultmovechance${i}/error.txt | grep "error" | grep "${j}" | awk '{print $9}' >> tmp.txt
  done
done

echo "#conflictmovechance,bur-normal,car-normal,mali-normal,bur-rescaled,car-rescaled,mali-rescaled"
sed 'N;N;N;N;N;N;s/\n/,/g' tmp.txt
