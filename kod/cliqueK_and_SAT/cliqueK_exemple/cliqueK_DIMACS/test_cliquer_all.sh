#!/bin/bash
# test_cliquer_all.sh - testiraj sve clique instance sa Cliquer-om

echo "Cliquer DIMACS Clique Benchmark Test"
echo "===================================="
echo "Started: $(date)"
echo ""

results_file="cliquer_results.txt"
echo "Cliquer DIMACS Clique Benchmark Results" > "$results_file"
echo "=======================================" >> "$results_file"
echo "Started: $(date)" >> "$results_file"
echo "" >> "$results_file"

# Counters
solved_count=0
timeout_count=0
error_count=0
total_time=0

test_clique_file() {
    local file="$1"
    local basename_file=$(basename "$file")
    
    echo "Testing: $basename_file"
    
    # Fajlovi za output
    cliquer_output="/tmp/cliquer_output_$$.txt"
    
    # Pokreni Cliquer sa merěnjem vremena i timeout
    start_time=$(date +%s%N)
    timeout 300 cliquer "$file" > "$cliquer_output" 2>&1  # 5 minuta timeout
    exit_code=$?
    end_time=$(date +%s%N)
    
    # Izračunaj vreme u sekundama
    time_ns=$((end_time - start_time))
    time_sec=$(echo "scale=3; $time_ns / 1000000000" | bc -l)
    
    # Parsiranje rezultata
    if [ $exit_code -eq 124 ]; then
        status="TIMEOUT"
        time_display="300.000+"
        clique_size="N/A"
        clique_weight="N/A"
        ((timeout_count++))
        
    elif [ $exit_code -eq 0 ]; then
        # Uspešno završen - parsuj rezultat
        if grep -q "size=" "$cliquer_output"; then
            # Izvuci clique size i weight iz poslednje linije
            result_line=$(grep "size=" "$cliquer_output" | tail -1)
            clique_size=$(echo "$result_line" | grep -o "size=[0-9]*" | grep -o "[0-9]*")
            clique_weight=$(echo "$result_line" | grep -o "weight=[0-9]*" | grep -o "[0-9]*")
            
            # Ako nema weight, onda je unweighted (weight = size)
            if [ -z "$clique_weight" ]; then
                clique_weight="$clique_size"
            fi
            
            status="SOLVED"
            time_display="${time_sec}s"
            total_time=$(echo "$total_time + $time_sec" | bc -l)
            ((solved_count++))
            
        else
            status="ERROR"
            time_display="${time_sec}s"
            clique_size="N/A"
            clique_weight="N/A"
            ((error_count++))
        fi
        
    else
        status="ERROR"
        time_display="${time_sec}s"
        clique_size="N/A"
        clique_weight="N/A"
        ((error_count++))
        echo "    ERROR: exit_code=$exit_code"
    fi
    
    # Live ispis
    echo "  Result: $status, Clique size: $clique_size, Time: $time_display"
    
    # Zapišи rezultat u fajl (formatiranje tabele)
    printf "%-25s | %-8s | %-4s | %-6s | %10s\n" \
        "$basename_file" "$status" "$clique_size" "$clique_weight" "$time_display" >> "$results_file"
    
    # Cleanup
    rm -f "$cliquer_output"
}

# Header za tabelu
printf "%-25s | %-8s | %-4s | %-6s | %10s\n" \
    "File" "Status" "Size" "Weight" "Time" >> "$results_file"
echo "------------------------------------------------------------------------" >> "$results_file"

# Testiraj sve .clq.txt fajlove
total_instances=0
if [ -d "CLIQUE_DIMACS" ]; then
    for file in CLIQUE_DIMACS/*.clq.txt; do
        if [ -f "$file" ]; then
            ((total_instances++))
            test_clique_file "$file"
        fi
    done
else
    echo "Error: CLIQUE_DIMACS direktorijum ne postoji!"
    exit 1
fi

# Finalne statistike
echo ""
echo "=== FINAL STATISTICS ==="
echo "Solved instances:    $solved_count"
echo "Timeout instances:   $timeout_count"
echo "Error instances:     $error_count"
echo "Total instances:     $total_instances"

if [ $solved_count -gt 0 ]; then
    avg_time=$(echo "scale=3; $total_time / $solved_count" | bc -l)
    echo "Total solving time:  ${total_time}s"
    echo "Average solve time:  ${avg_time}s"
fi

# Zapišи statistike u fajl
echo "" >> "$results_file"
echo "FINAL STATISTICS:" >> "$results_file"
echo "=================" >> "$results_file"
echo "Solved instances:    $solved_count" >> "$results_file"
echo "Timeout instances:   $timeout_count" >> "$results_file"
echo "Error instances:     $error_count" >> "$results_file"
echo "Total instances:     $total_instances" >> "$results_file"

if [ $solved_count -gt 0 ]; then
    echo "Total solving time:  ${total_time}s" >> "$results_file"
    echo "Average solve time:  ${avg_time}s" >> "$results_file"
fi

echo "Completed: $(date)" >> "$results_file"

echo ""
echo "Results saved in: $results_file"
echo ""
echo "Quick analysis commands:"
echo "- View all results: cat $results_file"
echo "- Only solved: grep 'SOLVED' $results_file"
echo "- Only timeouts: grep 'TIMEOUT' $results_file"
echo "- Largest cliques: grep 'SOLVED' $results_file | sort -k3 -nr | head -5"
echo "- Slowest solved: grep 'SOLVED' $results_file | sort -k5 -nr | head -5"
