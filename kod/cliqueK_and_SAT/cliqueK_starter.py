#!/usr/bin/env python3

import os
import subprocess
import time
import re
from pathlib import Path
import argparse
from typing import Tuple, Dict, List, Set

def is_sat_output(stdout: str) -> bool:
    """Check if URSA output indicates a solution was found."""
    if "--> Solution" in stdout:
        return True
    elif "[Solving time:" in stdout and "[Formula size:" in stdout:
        if "0 solutions" not in stdout and "No solutions" not in stdout:
            return True
    return False

def is_unsat_output(stdout: str) -> bool:
    """Check if URSA output indicates no solution was found."""
    if "No solutions found" in stdout or re.search(r'\b0 solutions\b', stdout):
        return True
    if re.search(r'\[Number of solutions:\s*0\]', stdout):
        return True
    return False

def find_graph_files(graph_dir: str) -> List[str]:
    """Find all DIMACS graph files (.clq, .txt) in a directory (sorted)."""
    graph_files = []
    for root, dirs, files in os.walk(graph_dir):
        for file in files:
            if file.endswith('.clq') or file.endswith('.txt'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        first_lines = f.read(1000)
                        if 'p edge' in first_lines or 'p col' in first_lines or 'e ' in first_lines:
                            graph_files.append(filepath)
                except:
                    continue
    graph_files.sort()
    return graph_files

def extract_category(graph_file: str) -> str:
    """Extract category from parent directory name."""
    path_parts = Path(graph_file).parts
    for part in path_parts:
        if part.upper() in ['BROCK', 'KELLER', 'MANN', 'P_HAT', 'SAN', 'SANR', 'C-FAT', 'HAMMING', 'JOHNSON']:
            return part.upper()
    return "UNKNOWN"

def write_header(f, solver_template_name: str, reduction_template_name: str = None, save_urs: bool = False):
    """Write benchmark table header to output file."""
    f.write("URSA vs Cliquer Max Clique Benchmark Results\n")
    f.write("=============================================\n")
    f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    if save_urs:
        f.write(f"URS files saved to: urs_files\n")
        if reduction_template_name:
            f.write(f"Reduction files saved to: reduction_files\n")
    f.write("\n")

    header_parts = [
        f"{'Category':<12}",
        f"{'File':<35}",
        f"{'Vertices':<9}",
        f"{'Edges':<8}",
        f"{'URSA':<12}",
        f"{'Cliquer':<12}"
    ]

    if reduction_template_name:
        header_parts.append(f"{'Reduction':<12}")

    header_parts.extend([
        f"{'URSA Time':<10}",
        f"{'Cliquer Time':<12}"
    ])

    if reduction_template_name:
        header_parts.append(f"{'Red. Time':<10}")

    header_parts.extend([
        f"{'URSA Clique':<12}",
        f"{'Cliq. Clique':<12}"
    ])

    if reduction_template_name:
        header_parts.append(f"{'Red. Clique':<12}")

    if save_urs:
        header_parts.append(f"{'URS File':<25}")
        if reduction_template_name:
            header_parts.append(f"{'Reduction File':<25}")

    f.write(" | ".join(header_parts) + "\n")
    f.write("-" * (sum(len(part) for part in header_parts) + 3 * (len(header_parts) - 1)) + "\n")

def update_stats(stats: Dict, result: Dict, has_reduction: bool = False):
    """Update cumulative statistics with a single benchmark result."""
    stats["total"] += 1
    
    # Update URSA stats
    ursa_status_key = result['ursa_status'].lower()
    if ursa_status_key == 'found':
        stats['ursa']['found'] += 1
    elif ursa_status_key == 'not_found':
        stats['ursa']['not_found'] += 1
    elif ursa_status_key == 'timeout':
        stats['ursa']['timeout'] += 1
    else:
        stats['ursa']['error'] += 1
    
    # Update Cliquer stats
    cliquer_status_key = result['cliquer_status'].lower()
    if cliquer_status_key == 'found':
        stats['cliquer']['found'] += 1
    elif cliquer_status_key == 'timeout':
        stats['cliquer']['timeout'] += 1
    else:
        stats['cliquer']['error'] += 1
    
    # Update Reduction stats if applicable
    if has_reduction:
        red_status_key = result['reduction_status'].lower()
        if red_status_key == 'found':
            stats['reduction']['found'] += 1
        elif red_status_key == 'not_found':
            stats['reduction']['not_found'] += 1
        elif red_status_key == 'timeout':
            stats['reduction']['timeout'] += 1
        else:
            stats['reduction']['error'] += 1

def write_final_statistics(f, stats: Dict, has_reduction: bool = False):
    """Write final statistics to output file."""
    f.write(f"\nFINAL STATISTICS:\n")
    f.write(f"=================\n\n")
    f.write(f"URSA Results:\n")
    f.write(f"Cliques found:     {stats['ursa']['found']}\n")
    f.write(f"Not found:         {stats['ursa']['not_found']}\n")
    f.write(f"Timeout:           {stats['ursa']['timeout']}\n")
    f.write(f"Error:             {stats['ursa']['error']}\n\n")
    
    f.write(f"Cliquer Results:\n")
    f.write(f"Cliques found:     {stats['cliquer']['found']}\n")
    f.write(f"Timeout:           {stats['cliquer']['timeout']}\n")
    f.write(f"Error:             {stats['cliquer']['error']}\n\n")
    
    if has_reduction:
        f.write(f"Reduction Results:\n")
        f.write(f"Cliques found:     {stats['reduction']['found']}\n")
        f.write(f"Not found:         {stats['reduction']['not_found']}\n")
        f.write(f"Timeout:           {stats['reduction']['timeout']}\n")
        f.write(f"Error:             {stats['reduction']['error']}\n\n")
    
    f.write(f"Total instances:   {stats['total']}\n")
    f.write(f"Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

def filter_files(graph_files: List[str], processed_files: Set[str], continue_mode: bool) -> List[str]:
    """Filter out already processed files if continue mode is active."""
    files_to_process = []
    skipped_count = 0
    for graph_file in graph_files:
        file_name = os.path.basename(graph_file)
        if continue_mode and file_name in processed_files:
            skipped_count += 1
        else:
            files_to_process.append(graph_file)

    if continue_mode and skipped_count > 0:
        print(f"Skipping {skipped_count} already processed files")
    print(f"Will process {len(files_to_process)} files")
    return files_to_process

def prepare_output_file(output_file: str, continue_mode: bool) -> str:
    """Prepare output file for writing (clear old final statistics if continuing)."""
    file_mode = "a" if continue_mode and os.path.exists(output_file) else "w"
    if file_mode == "a":
        with open(output_file, "r") as f:
            existing_lines = f.readlines()
        final_stats_index = next((i for i, line in enumerate(existing_lines) if "FINAL STATISTICS:" in line), -1)
        if final_stats_index > 0:
            existing_lines = existing_lines[:final_stats_index]
        with open(output_file, "w") as f:
            f.writelines(existing_lines)
    return file_mode

class URSACliqueBenchmark:
    def __init__(self, ursa_path="./ursa", cliquer_path="cliquer", timeout=120, 
                 solver_template=None, reduction_template=None, save_urs=False, 
                 urs_output_dir="urs_files", reduction_output_dir="reduction_files",
                 continue_mode=False, output_file="clique_benchmark_results.txt"):
        self.ursa_path = ursa_path
        self.cliquer_path = cliquer_path
        self.timeout = timeout
        
        if solver_template is None:
            raise ValueError("Solver template is required")
        self.solver_template = solver_template
        
        self.reduction_template = reduction_template
        
        self.save_urs = save_urs
        self.urs_output_dir = urs_output_dir
        self.reduction_output_dir = reduction_output_dir
        
        self.continue_mode = continue_mode
        self.output_file = output_file
        self.processed_files = set()
        self.existing_stats = None
        self.existing_header = None
        
        if self.save_urs:
            os.makedirs(self.urs_output_dir, exist_ok=True)
            if self.reduction_template:
                os.makedirs(self.reduction_output_dir, exist_ok=True)
    
    def _initialize_empty_stats(self) -> Dict:
        """Initialize an empty statistics dictionary."""
        return {
            'total': 0,
            'ursa': {'found': 0, 'not_found': 0, 'timeout': 0, 'error': 0},
            'cliquer': {'found': 0, 'timeout': 0, 'error': 0},
            'reduction': {'found': 0, 'not_found': 0, 'timeout': 0, 'error': 0}
        }
    
    def _extract_header_lines(self, data_lines: List[str]) -> List[str]:
        """Extract header lines from data (until separator line)."""
        for i, line in enumerate(data_lines):
            if '-----' in line:
                return data_lines[:i+1]
        return []
    
    def _extract_processed_filenames(self, data_lines: List[str]) -> Set[str]:
        """Extract processed file names from result lines."""
        processed_files = set()
        for line in data_lines:
            if '|' in line and ('.clq' in line or '.txt' in line):
                parts = line.split('|')
                if len(parts) >= 2:
                    file_part = parts[1].strip()
                    if '.clq' in file_part or '.txt' in file_part:
                        processed_files.add(file_part)
        return processed_files
    
    def _parse_statistics_section(self, stats_lines: List[str]) -> Dict:
        """Parse statistics from the statistics section."""
        stats = self._initialize_empty_stats()
        current_context = None
        
        for line in stats_lines:
            line_stripped = line.strip()
            
            if "URSA Results:" in line:
                current_context = "ursa"
            elif "Cliquer Results:" in line:
                current_context = "cliquer"
            elif "Reduction Results:" in line:
                current_context = "reduction"
            elif "Total instances:" in line:
                try:
                    total_str = line.split(':', 1)[1].strip()
                    stats['total'] = int(total_str)
                except:
                    pass
                current_context = None
            
            if current_context and ("found:" in line.lower() or "timeout:" in line.lower() or "error:" in line.lower()):
                self._parse_stat_line(stats, current_context, line)
        
        return stats
    
    def _parse_stat_line(self, stats: Dict, context: str, line: str):
        """Parse a single statistics line and update the stats dictionary."""
        try:
            if "cliques found:" in line.lower():
                num_str = line.split(':', 1)[1].strip()
                stats[context]['found'] = int(num_str)
            elif "not found:" in line.lower():
                num_str = line.split(':', 1)[1].strip()
                stats[context]['not_found'] = int(num_str)
            elif "timeout:" in line.lower():
                num_str = line.split(':', 1)[1].strip()
                stats[context]['timeout'] = int(num_str)
            elif "error:" in line.lower():
                num_str = line.split(':', 1)[1].strip()
                stats[context]['error'] = int(num_str)
        except (ValueError, IndexError):
            pass
    
    def _print_existing_results_summary(self, processed_files: Set[str], existing_stats: Dict):
        """Print summary of loaded existing results."""
        print(f"Found {len(processed_files)} already processed files in {self.output_file}")
        if existing_stats['total'] > 0:
            print(f"Existing statistics: {existing_stats['total']} total instances")
    
    def load_existing_results(self) -> Tuple[Set[str], Dict, List[str]]:
        """Load existing results from file and return processed files, stats, and header lines."""
        processed_files = set()
        existing_stats = self._initialize_empty_stats()
        header_lines = []
        
        if not os.path.exists(self.output_file):
            return processed_files, existing_stats, header_lines
        
        try:
            with open(self.output_file, 'r') as f:
                lines = f.readlines()
            
            # Find where final statistics begin
            final_stats_index = -1
            for i, line in enumerate(lines):
                if "FINAL STATISTICS:" in line:
                    final_stats_index = i
                    break
            
            if final_stats_index == -1:
                data_lines = lines
            else:
                data_lines = lines[:final_stats_index]
                stats_lines = lines[final_stats_index:]
                existing_stats = self._parse_statistics_section(stats_lines)
            
            header_lines = self._extract_header_lines(data_lines)
            processed_files = self._extract_processed_filenames(data_lines)
            self._print_existing_results_summary(processed_files, existing_stats)
            
        except Exception as e:
            print(f"Warning: Could not fully parse existing results: {e}")
        
        return processed_files, existing_stats, header_lines
    
    def load_or_init_stats(self) -> Tuple[Set[str], Dict, List[str]]:
        """Load existing results if continue mode is enabled, otherwise initialize fresh stats."""
        if self.continue_mode:
            return self.load_existing_results()
        else:
            return set(), self._initialize_empty_stats(), []

    def parse_dimacs_graph(self, content: str) -> Tuple[int, int, List[Tuple[int, int]]]:
        """Parse DIMACS graph format (p edge format). Returns (num_vertices, num_edges, edges)."""
        lines = content.strip().split('\n')
        num_vertices = 0
        num_edges = 0
        edges = []
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('c'):
                continue
                
            # Header line
            if line.startswith('p edge') or line.startswith('p col'):
                parts = line.split()
                num_vertices = int(parts[2])
                num_edges = int(parts[3])
                continue
                
            # Edge lines
            if line.startswith('e '):
                parts = line.split()
                if len(parts) >= 3:
                    v1 = int(parts[1])
                    v2 = int(parts[2])
                    edges.append((v1, v2))
                    
        return num_vertices, num_edges, edges

    def generate_urs_code(self, num_vertices: int, edges: List[Tuple[int, int]], template: str) -> str:
        """Generate URS code for Max Clique problem."""
        # Create adjacency matrix
        urs_code = f"""nN = {num_vertices};

// Initialize adjacency matrix
for(i=0; i<nN; i++) {{
    for(j=0; j<nN; j++) {{
        bEdge[i][j] = false;
    }}
}}

// Add edges (convert from 1-indexed to 0-indexed)
"""
        
        # Add each edge (convert from 1-indexed to 0-indexed)
        for v1, v2 in edges:
            v1_idx = v1 - 1  # Convert to 0-indexed
            v2_idx = v2 - 1  # Convert to 0-indexed
            urs_code += f"bEdge[{v1_idx}][{v2_idx}] = true;\n"
            urs_code += f"bEdge[{v2_idx}][{v1_idx}] = true;\n"  # Graph is undirected
        
        # Add template logic
        urs_code += "\n" + template + "\n"
        return urs_code
    
    def save_urs_code(self, urs_code: str, original_filename: str, output_dir: str, suffix: str = "") -> str:
        """Save the generated URS code to a file and return the file path."""
        base_name = Path(original_filename).stem
        urs_filename = f"{base_name}{suffix}.urs"
        urs_filepath = os.path.join(output_dir, urs_filename)
        
        try:
            with open(urs_filepath, 'w') as f:
                f.write(urs_code)
            return urs_filepath
        except Exception as e:
            print(f"Error saving URS code to {urs_filepath}: {e}")
            return None
    
    def run_ursa(self, urs_code: str, debug_name: str = "") -> Tuple[str, float, int]:
        """Run URSA with a given URS code. Returns (status, time, clique_size)."""
        try:
            start_time = time.time()
            process = subprocess.Popen(
                [self.ursa_path, "-q"], 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(input=urs_code, timeout=self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return "TIMEOUT", self.timeout, 0

            end_time = time.time()
            actual_elapsed = end_time - start_time

            if process.returncode == 0:
                # Try to find clique size from output
                clique_size = 0
                
                # Example: if template outputs "Clique size: X"
                size_match = re.search(r'Clique size:\s*(\d+)', stdout)
                if not size_match:
                    size_match = re.search(r'Maximum clique:\s*(\d+)', stdout)
                if not size_match:
                    size_match = re.search(r'Solution.*?(\d+)', stdout)
                
                if size_match:
                    clique_size = int(size_match.group(1))
                
                if is_sat_output(stdout) or clique_size > 0:
                    return "FOUND", actual_elapsed, clique_size
                elif is_unsat_output(stdout):
                    return "NOT_FOUND", actual_elapsed, 0
                else:
                    return "UNKNOWN", actual_elapsed, 0
            else:
                return "ERROR", actual_elapsed, 0

        except Exception as e:
            print(f"URSA error: {e}")
            return "ERROR", 0.0, 0

    def run_cliquer(self, graph_file: str) -> Tuple[str, float, int]:
        """Run Cliquer on a graph file. Returns (status, time, clique_size)."""
        try:
            start_time = time.time()
            
            process = subprocess.Popen(
                [self.cliquer_path, graph_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            
            # Parse Cliquer output - look for "size=X" pattern
            clique_size = 0
            
            # Look for "size=X" pattern from cliquer output
            size_match = re.search(r'size=(\d+)', stdout)
            if size_match:
                clique_size = int(size_match.group(1))
            
            if process.returncode == 0 and clique_size > 0:
                return "FOUND", elapsed_time, clique_size
            elif process.returncode == 0 and clique_size == 0:
                return "NOT_FOUND", elapsed_time, 0
            else:
                return "ERROR", elapsed_time, 0
                
        except subprocess.TimeoutExpired:
            process.kill()
            return "TIMEOUT", self.timeout, 0
        except Exception as e:
            print(f"Cliquer error: {e}")
            return "ERROR", 0.0, 0
    
    def run_with_template(self, num_vertices: int, edges: List[Tuple[int, int]], 
                         template: str, save_dir: str = None, suffix: str = "",
                         label: str = "URSA", verbose: bool = False, 
                         original_filename: str = None) -> Tuple[str, float, int]:
        """Generate URS code, optionally save it, run URSA solver, and return (status, elapsed_time, clique_size)."""
        urs_code = self.generate_urs_code(num_vertices, edges, template)

        if save_dir and original_filename:
            filepath = self.save_urs_code(urs_code, original_filename, save_dir, suffix)
            if filepath and verbose:
                print(f"{label} code saved to: {filepath}")

        status, elapsed, clique_size = self.run_ursa(urs_code, label if verbose else "")
        if verbose:
            print(f"{label}: {status} (size={clique_size}, time={elapsed:.6f}s)")

        return status, elapsed, clique_size
    
    def benchmark_file(self, graph_file: str, verbose: bool = True) -> Dict[str, any]:
        """Benchmark a single graph file with URSA, Cliquer, and optionally URSA Reduction."""
        file_name = os.path.basename(graph_file)
        if self.continue_mode and file_name in self.processed_files:
            if verbose:
                print(f"Skipping already processed: {file_name}")
            return None
        
        if verbose:
            print(f"Testing: {file_name}")
        
        # Read and parse graph file
        try:
            with open(graph_file, 'r') as f:
                graph_content = f.read()
            num_vertices, num_edges, edges = self.parse_dimacs_graph(graph_content)
            if verbose:
                print(f"Parsed: {num_vertices} vertices, {num_edges} edges")
        except Exception as e:
            if verbose:
                print(f"Error parsing {graph_file}: {e}")
            return None
        
        # Run URSA
        ursa_status, ursa_time, ursa_clique = self.run_with_template(
            num_vertices, edges,
            template=self.solver_template,
            save_dir=self.urs_output_dir if self.save_urs else None,
            label="URSA",
            verbose=verbose,
            original_filename=file_name
        )
        
        # Run Cliquer
        cliquer_status, cliquer_time, cliquer_clique = self.run_cliquer(graph_file)
        if verbose:
            print(f"Cliquer: {cliquer_status} (size={cliquer_clique}, time={cliquer_time:.6f}s)")
        
        result = {
            'file': file_name,
            'vertices': num_vertices,
            'edges': num_edges,
            'ursa_status': ursa_status,
            'ursa_time': ursa_time,
            'ursa_clique': ursa_clique,
            'cliquer_status': cliquer_status,
            'cliquer_time': cliquer_time,
            'cliquer_clique': cliquer_clique
        }
        
        # Run URSA Reduction if template provided
        if self.reduction_template:
            reduction_status, reduction_time, reduction_clique = self.run_with_template(
                num_vertices, edges,
                template=self.reduction_template,
                save_dir=self.reduction_output_dir if self.save_urs else None,
                suffix="_reduction",
                label="Reduction",
                verbose=verbose,
                original_filename=file_name
            )
            result['reduction_status'] = reduction_status
            result['reduction_time'] = reduction_time
            result['reduction_clique'] = reduction_clique
        
        return result
    
    def benchmark_directory(self, graph_dir: str, output_file: str = "clique_benchmark_results.txt"):
        """Benchmark all graph files in a directory, with support for continue mode."""
        
        self.processed_files, self.existing_stats, self.existing_header = self.load_or_init_stats()
        
        graph_files = find_graph_files(graph_dir)
        print(f"Found {len(graph_files)} graph files")
        
        files_to_process = filter_files(graph_files, self.processed_files, self.continue_mode)
        
        if self.save_urs:
            print(f"URS files will be saved to: {self.urs_output_dir}")
            if self.reduction_template:
                print(f"Reduction files will be saved to: {self.reduction_output_dir}")
        
        # Fresh stats for this run
        stats = self._initialize_empty_stats()
        
        file_mode = prepare_output_file(output_file, self.continue_mode)
        
        with open(output_file, file_mode) as f:
            if file_mode == "w":
                solver_name = "solver_template"
                reduction_name = "reduction_template" if self.reduction_template else None
                write_header(f, solver_name, reduction_name, self.save_urs)
            
            # Benchmark each file
            for i, graph_file in enumerate(files_to_process, 1):
                print(f"Testing: {os.path.basename(graph_file)}, {i}/{len(files_to_process)} ...", end='', flush=True)
                
                start_time = time.time()
                result = self.benchmark_file(graph_file, verbose=False)
                end_time = time.time()
                
                if result is None:
                    print(" (SKIPPED or FAILED)")
                    continue
                
                total_time = end_time - start_time
                print(f" ({total_time:.6f}s)")
                
                update_stats(stats, result, has_reduction=bool(self.reduction_template))
                category = extract_category(graph_file)
                
                # Write result line
                line_parts = [
                    f"{category:<12}",
                    f"{result['file']:<35}",
                    f"{result['vertices']:<9}",
                    f"{result['edges']:<8}",
                    f"{result['ursa_status']:<12}",
                    f"{result['cliquer_status']:<12}"
                ]
                
                if self.reduction_template:
                    line_parts.append(f"{result['reduction_status']:<12}")
                
                line_parts.extend([
                    f"{result['ursa_time']:<10.6f}",
                    f"{result['cliquer_time']:<12.6f}"
                ])
                
                if self.reduction_template:
                    line_parts.append(f"{result['reduction_time']:<10.6f}")
                
                line_parts.extend([
                    f"{result['ursa_clique']:<12}",
                    f"{result['cliquer_clique']:<12}"
                ])
                
                if self.reduction_template:
                    line_parts.append(f"{result['reduction_clique']:<12}")
                
                if self.save_urs:
                    urs_filename = os.path.basename(result.get('urs_file', ''))
                    line_parts.append(f"{urs_filename:<25}")
                    
                    if self.reduction_template:
                        reduction_filename = os.path.basename(result.get('reduction_file', ''))
                        line_parts.append(f"{reduction_filename:<25}")
                
                f.write(" | ".join(line_parts) + "\n")
                f.flush()
            
            # Combine and write final statistics
            combined_stats = {
                'total': self.existing_stats['total'] + stats['total'],
                'ursa': {k: self.existing_stats['ursa'][k] + stats['ursa'][k] for k in self.existing_stats['ursa']},
                'cliquer': {k: self.existing_stats['cliquer'][k] + stats['cliquer'][k] for k in self.existing_stats['cliquer']},
                'reduction': {k: self.existing_stats['reduction'][k] + stats['reduction'][k] for k in self.existing_stats['reduction']}
            }
            
            write_final_statistics(f, combined_stats, has_reduction=bool(self.reduction_template))
        
        if self.continue_mode:
            print(f"Benchmark completed. Added {stats['total']} new results.")
            print(f"Total instances in {output_file}: {combined_stats['total']}")
        else:
            print(f"Benchmark completed. Results saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='URSA vs Cliquer Max Clique Benchmark')
    parser.add_argument('graph_dir', nargs='?', help='Directory containing graph files (.clq, .txt)')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout in seconds')
    parser.add_argument('--output', default='cliqueK_results.txt', help='Output file')
    parser.add_argument('--single-file', help='Test single graph file instead of directory')
    parser.add_argument('--solver-template', required=True, help='Path to file containing URS solver template (REQUIRED)')
    parser.add_argument('--reduction-template', help='Path to file containing URS reduction template (OPTIONAL)')
    parser.add_argument('--save-urs', action='store_true', help='Save generated URS code to files')
    parser.add_argument('--continue', dest='continue_mode', action='store_true', 
                       help='Continue from previous run - skip already processed files and append new results')
    
    args = parser.parse_args()
    
    # Load solver template
    try:
        with open(args.solver_template, 'r') as f:
            solver_template = f.read()
        print(f"Loaded solver template from: {args.solver_template}")
    except Exception as e:
        print(f"Error loading solver template {args.solver_template}: {e}")
        return
    
    # Load reduction template (optional)
    reduction_template = None
    if args.reduction_template:
        try:
            with open(args.reduction_template, 'r') as f:
                reduction_template = f.read()
            print(f"Loaded reduction template from: {args.reduction_template}")
        except Exception as e:
            print(f"Error loading reduction template {args.reduction_template}: {e}")
            return
    
    # Create benchmark object
    benchmark = URSACliqueBenchmark(
        ursa_path='./ursa',
        cliquer_path='cliquer', 
        timeout=args.timeout,
        solver_template=solver_template,
        reduction_template=reduction_template,
        save_urs=args.save_urs,
        urs_output_dir='cliqueK_saved_files',
        reduction_output_dir='cliqueK_reduction_saved_files',
        continue_mode=args.continue_mode,
        output_file=args.output
    )
    
    # Run benchmark
    if args.single_file:
        # Continue mode for single file
        if args.continue_mode:
            benchmark.processed_files, _, _ = benchmark.load_existing_results()
        
        result = benchmark.benchmark_file(args.single_file, verbose=True)
        if result:
            print("\nResults:")
            print(f"  Vertices: {result['vertices']}, Edges: {result['edges']}")
            print(f"  URSA: {result['ursa_status']}, Clique size: {result['ursa_clique']}, Time: {result['ursa_time']:.6f}s")
            print(f"  Cliquer: {result['cliquer_status']}, Clique size: {result['cliquer_clique']}, Time: {result['cliquer_time']:.6f}s")
            
            if 'reduction_status' in result:
                print(f"  Reduction: {result['reduction_status']}, Clique size: {result['reduction_clique']}, Time: {result['reduction_time']:.6f}s")
    else:
        if not args.graph_dir:
            print("Error: graph_dir is required when not using --single-file")
            return
        benchmark.benchmark_directory(args.graph_dir, args.output)

if __name__ == "__main__":
    main()
