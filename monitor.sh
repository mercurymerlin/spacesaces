while true; do
    clear
    echo "=== CPU and Memory Usage ==="
    top -bn1 | head -n 5

    echo -e "\n=== Disk I/O ==="
    iostat -x 1 2 | tail -n 4

    # echo -e "\n=== Network Usage ==="
    # ifstat -t 1 1

    echo -e "\n=== SQLite Activity ==="
    lsof | grep sqlite | wc -l | xargs echo "Open SQLite connections:"

    echo -e "\n=== Process Info ==="
    ps aux --sort=-%cpu | grep python | grep -v grep
    # ps aux --sort=-%cpu | head -n 11 | awk 'NR==1 || /python/'

    sleep 60
done