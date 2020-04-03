echo "house"
cat $1 | grep house | wc -l
echo "park"
cat $1 | grep park | wc -l
echo "leisure"
cat $1 | grep leisure | wc -l
echo "school"
cat $1 | grep school | wc -l
echo "shopping"
cat $1 | grep shopping | wc -l
echo "supermarket"
cat $1 | grep supermarket | wc -l
echo "hospital"
cat $1 | grep hospital | wc -l

