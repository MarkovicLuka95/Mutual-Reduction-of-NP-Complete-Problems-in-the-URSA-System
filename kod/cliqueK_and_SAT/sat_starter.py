#!/usr/bin/env python3

import os
import subprocess
import time
import re
from pathlib import Path
import argparse
from typing import Tuple, Dict, List, Set

def is_sat_output(stdout: str) -> bool:
    """Check if URSA output indicates SAT."""
    # Prvo proveri eksplicitne poruke
    if "--> Solution" in stdout:
        return True
    elif "[Solving time:" in stdout and "[Formula size:" in stdout:
        # Ako ima [Solving time:] i [Formula size:] ali nema "0 solutions" ili "No solutions"
        if "0 solutions" not in stdout and "No solutions" not in stdout:
            return True
    return False

def is_unsat_output(stdout: str) -> bool:
    """Check if URSA output indicates UNSAT."""
    # Postojeći uzorci
    if "No solutions found" in stdout or re.search(r'\b0 solutions\b', stdout):
        return True
    
    # Novi uzorak za format "[Number of solutions: 0]"
    if re.search(r'\[Number of solutions:\s*0\]', stdout):
        return True
    
    return False

def find_dimacs_files(dimacs_dir: str) -> List[str]:
    """Find all DIMACS .cnf files in a directory (sorted)."""
    dimacs_files = []
    for root, dirs, files in os.walk(dimacs_dir):
        for file in files:
            if file.endswith('.cnf'):
                dimacs_files.append(os.path.join(root, file))
    dimacs_files.sort()
    return dimacs_files

def extract_category(dimacs_file: str) -> str:
    """Extract category from parent directory name."""
    path_parts = Path(dimacs_file).parts
    for part in path_parts:
        if part.upper() in ['AIM', 'DUBOIS', 'PHOLE', 'GCP', 'PARITY', 'JNH']:
            return part.upper()
    return "UNKNOWN"

def write_header(f, solver_template_name: str, reduction_template_name: str = None, save_urs: bool = False):
    """Write benchmark table header to output file."""
    f.write(f"URSA Benchmark ({solver_template_name}) vs MiniSat")
    if reduction_template_name:
        f.write(f" vs URSA Reduction ({reduction_template_name})")
    f.write("\n")
    f.write("===============================================\n")
    f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    if save_urs:
        f.write("URS files will be saved to: urs_files\n")
        if reduction_template_name:
            f.write("Reduction files will be saved to: reduction_files\n")
    f.write("\n")

    # Ispravljen redosled header-a - reduction ide odmah posle MiniSat
    header_parts = [
        f"{'Category':<12}",
        f"{'File':<35}",
        f"{'Variables':<9}",
        f"{'Clauses':<8}",
        f"{'URSA':<8}",
        f"{'MiniSat':<8}",
    ]

    if reduction_template_name:
        header_parts.append(f"{'Reduction':<10}")

    header_parts.extend([
        f"{'URSA Time':<10}",
        f"{'MiniSat Time':<12}",
    ])

    if reduction_template_name:
        header_parts.append(f"{'Reduction Time':<14}")

    f.write(" | ".join(header_parts) + "\n")
    f.write("-" * (sum(len(part) for part in header_parts) + 3 * (len(header_parts) - 1)) + "\n")

def update_stats(stats: Dict, result: Dict, has_reduction: bool = False):
    """Update cumulative statistics with a single benchmark result."""
    stats["total"] += 1
    stats["ursa"][result["ursa_status"]] += 1
    stats["minisat"][result["minisat_status"]] += 1
    if has_reduction:
        stats["reduction"][result["reduction_status"]] += 1

def write_final_statistics(f, stats: Dict, has_reduction: bool = False):
    """Write final statistics to output file."""
    f.write("\nFINAL STATISTICS:\n")
    f.write("=================\n\n")

    f.write("URSA Results:\n")
    f.write(f"SAT instances:     {stats['ursa']['SAT']}\n")
    f.write(f"UNSAT instances:   {stats['ursa']['UNSAT']}\n")
    f.write(f"UNKNOWN instances: {stats['ursa']['UNKNOWN']}\n")
    f.write(f"TIMEOUT instances: {stats['ursa']['TIMEOUT']}\n")
    f.write(f"ERROR instances:   {stats['ursa']['ERROR']}\n\n")

    f.write("MiniSat Results:\n")
    f.write(f"SAT instances:     {stats['minisat']['SAT']}\n")
    f.write(f"UNSAT instances:   {stats['minisat']['UNSAT']}\n")
    f.write(f"TIMEOUT instances: {stats['minisat']['TIMEOUT']}\n")
    f.write(f"ERROR instances:   {stats['minisat']['ERROR']}\n\n")

    if has_reduction:
        f.write("Reduction Results:\n")
        f.write(f"SAT instances:     {stats['reduction']['SAT']}\n")
        f.write(f"UNSAT instances:   {stats['reduction']['UNSAT']}\n")
        f.write(f"UNKNOWN instances: {stats['reduction']['UNKNOWN']}\n")
        f.write(f"TIMEOUT instances: {stats['reduction']['TIMEOUT']}\n")
        f.write(f"ERROR instances:   {stats['reduction']['ERROR']}\n\n")

    f.write(f"Total instances:   {stats['total']}\n")
    f.write(f"Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

def filter_files(dimacs_files: List[str], processed_files: Set[str], continue_mode: bool) -> List[str]:
    """Filter out already processed files if continue mode is active."""
    files_to_process = []
    skipped_count = 0
    for dimacs_file in dimacs_files:
        file_name = os.path.basename(dimacs_file)
        if continue_mode and file_name in processed_files:
            skipped_count += 1
        else:
            files_to_process.append(dimacs_file)

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

class URSASATBenchmark:
    def __init__(self, ursa_path="./ursa", minisat_path="minisat", timeout=120, 
                 solver_template=None, reduction_template=None, save_urs=False, 
                 urs_output_dir="urs_files", reduction_output_dir="reduction_files",
                 continue_mode=False, output_file="SAT_benchmark_results.txt"):
        
        """Initialize URSASATBenchmark with configuration parameters."""
        self.ursa_path = ursa_path
        self.minisat_path = minisat_path
        self.timeout = timeout
        
        if solver_template is None:
            raise ValueError("Solver template is required")
        self.solver_template = solver_template
        self.reduction_template = reduction_template
        
        self.save_urs = save_urs
        self.urs_output_dir = urs_output_dir
        self.reduction_output_dir = reduction_output_dir
        
        # Continue mode additions
        self.continue_mode = continue_mode
        self.output_file = output_file
        self.processed_files = set()
        self.existing_stats = None
        self.existing_header = None
        
        # Create directories for URS files if they don't exist
        if self.save_urs:
            os.makedirs(self.urs_output_dir, exist_ok=True)
            if self.reduction_template:
                os.makedirs(self.reduction_output_dir, exist_ok=True)
    
    def load_existing_results(self) -> Tuple[Set[str], Dict, List[str]]:
        """
        Load existing results from file and return:
        - Set of processed files
        - Existing statistics
        - Header lines
        """
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
                # If no final stats, all lines are data
                data_lines = lines
            else:
                # Everything before final stats is data
                data_lines = lines[:final_stats_index]
                stats_lines = lines[final_stats_index:]
                
                existing_stats = self._parse_statistics_section(stats_lines)
            
            header_lines = self._extract_header_lines(data_lines)
            
            processed_files = self._extract_processed_filenames(data_lines)
            
            self._print_existing_results_summary(processed_files, existing_stats)
            
        except Exception as e:
            print(f"Warning: Could not fully parse existing results: {e}")
            import traceback
            traceback.print_exc()
        
        return processed_files, existing_stats, header_lines
      
    def _initialize_empty_stats(self) -> Dict:
        """Initialize an empty statistics dictionary."""
        return {
            'total': 0,
            'ursa': {'SAT': 0, 'UNSAT': 0, 'TIMEOUT': 0, 'ERROR': 0, 'UNKNOWN': 0},
            'minisat': {'SAT': 0, 'UNSAT': 0, 'TIMEOUT': 0, 'ERROR': 0},
            'reduction': {'SAT': 0, 'UNSAT': 0, 'TIMEOUT': 0, 'ERROR': 0, 'UNKNOWN': 0}
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
            if '|' in line and '.cnf' in line:
                # Parse result line
                parts = line.split('|')
                if len(parts) >= 2:
                    file_part = parts[1].strip()
                    if '.cnf' in file_part:
                        processed_files.add(file_part)
        return processed_files
        
    def _parse_statistics_section(self, stats_lines: List[str]) -> Dict:
        """Parse statistics from the statistics section."""
        stats = self._initialize_empty_stats()
        current_context = None
        
        for line in stats_lines:
            line_stripped = line.strip()
            
            # Detect context switch
            if "URSA Results:" in line:
                current_context = "ursa"
            elif "MiniSat Results:" in line:
                current_context = "minisat"
            elif "Reduction Results:" in line:
                current_context = "reduction"
            elif "Total instances:" in line:
                try:
                    total_str = line.split(':', 1)[1].strip()
                    stats['total'] = int(total_str)
                except:
                    pass
                current_context = None
            
            # Parse statistics based on current context
            if current_context and "instances:" in line:
                self._parse_stat_line(stats, current_context, line)
        
        return stats
        
    def _parse_stat_line(self, stats: Dict, context: str, line: str):
        """Parse a single statistics line and update the stats dictionary."""
        try:
            if "SAT instances:" in line:
                num_str = line.split(':', 1)[1].strip()
                stats[context]['SAT'] = int(num_str)
            elif "UNSAT instances:" in line:
                num_str = line.split(':', 1)[1].strip()
                stats[context]['UNSAT'] = int(num_str)
            elif "TIMEOUT instances:" in line:
                num_str = line.split(':', 1)[1].strip()
                stats[context]['TIMEOUT'] = int(num_str)
            elif "ERROR instances:" in line:
                num_str = line.split(':', 1)[1].strip()
                stats[context]['ERROR'] = int(num_str)
            elif "UNKNOWN instances:" in line and context in ['ursa', 'reduction']:
                num_str = line.split(':', 1)[1].strip()
                stats[context]['UNKNOWN'] = int(num_str)
        except (ValueError, IndexError) as e:
            print(f"WARNING: Could not parse line: {line.strip()}")
            
    def _print_existing_results_summary(self, processed_files: Set[str], existing_stats: Dict):
        """Print summary of loaded existing results."""
        print(f"Found {len(processed_files)} already processed files in {self.output_file}")
        
        if existing_stats['total'] > 0:
            print(f"Existing statistics: {existing_stats['total']} total instances")
            print(f"  URSA: SAT={existing_stats['ursa']['SAT']}, UNSAT={existing_stats['ursa']['UNSAT']}, "
                  f"TIMEOUT={existing_stats['ursa']['TIMEOUT']}, ERROR={existing_stats['ursa']['ERROR']}, "
                  f"UNKNOWN={existing_stats['ursa']['UNKNOWN']}")
            print(f"  MiniSat: SAT={existing_stats['minisat']['SAT']}, UNSAT={existing_stats['minisat']['UNSAT']}, "
                  f"TIMEOUT={existing_stats['minisat']['TIMEOUT']}, ERROR={existing_stats['minisat']['ERROR']}")
            
            if any(existing_stats['reduction'].values()):
                print(f"  Reduction: SAT={existing_stats['reduction']['SAT']}, UNSAT={existing_stats['reduction']['UNSAT']}, "
                      f"TIMEOUT={existing_stats['reduction']['TIMEOUT']}, ERROR={existing_stats['reduction']['ERROR']}, "
                      f"UNKNOWN={existing_stats['reduction']['UNKNOWN']}")
    
    def load_or_init_stats(self) -> Tuple[Set[str], Dict, List[str]]:
        """Load existing results if continue mode is enabled, otherwise initialize fresh stats."""
        if self.continue_mode:
            processed_files, existing_stats, existing_header = self.load_existing_results()
        else:
            processed_files = set()
            existing_stats = {
                "total": 0,
                "ursa": {"SAT": 0, "UNSAT": 0, "TIMEOUT": 0, "ERROR": 0, "UNKNOWN": 0},
                "minisat": {"SAT": 0, "UNSAT": 0, "TIMEOUT": 0, "ERROR": 0},
                "reduction": {"SAT": 0, "UNSAT": 0, "TIMEOUT": 0, "ERROR": 0, "UNKNOWN": 0},
            }
            existing_header = []
        return processed_files, existing_stats, existing_header

    def parse_dimacs(self, dimacs_content: str) -> Tuple[int, int, List[List[int]]]:
        """Parse DIMACS CNF content and return (num_vars, num_clauses, clauses)."""
        lines = dimacs_content.strip().split('\n')
        num_vars = 0
        num_clauses = 0
        clauses = []
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('c') or line.startswith('%'):
                continue
                
            # Header line
            if line.startswith('p cnf'):
                parts = line.split()
                num_vars = int(parts[2])
                num_clauses = int(parts[3])
                continue
                
            # Clauses
            if line and not line.startswith('p'):
                literals = [int(x) for x in line.split() if x != '0']
                if literals:  # Add only non-empty clauses
                    clauses.append(literals)
                    
        return num_vars, num_clauses, clauses

    def generate_urs_code(self, num_vars: int, num_clauses: int, clauses: List[List[int]], template: str) -> str:
        """Generate URS code from parsed DIMACS data using the provided template."""
        # Ovo je identično kao u staroj verziji
        urs_code = f"""nN = {num_vars};
nClauses = {num_clauses};

for(ni=0; ni<nClauses; ni++) {{
    for(nj=0; nj<2*nN; nj++) {{
        bC[ni][nj] = false;
    }}
}}

"""
        
        # Add each clause
        for clause_idx, clause in enumerate(clauses):
            for literal in clause:
                if literal > 0:
                    # Positive literal (1-indexed in DIMACS, 0-indexed in URSA)
                    var_index = literal - 1  # Convert to 0-indexed
                    urs_code += f"bC[{clause_idx}][{2 * var_index}] = true;\n"
                else:
                    # Negative literal (1-indexed in DIMACS, 0-indexed in URSA)  
                    var_index = abs(literal) - 1  # Convert to 0-indexed
                    urs_code += f"bC[{clause_idx}][{2 * var_index + 1}] = true;\n"
        
        # Add template logic
        urs_code += "\n" + template + "\n"
        return urs_code

    def save_urs_code(self, urs_code: str, original_filename: str, output_dir: str, suffix: str = "") -> str:
        """Save the generated URS code to a file and return the file path."""
        # Generate the filename based on the original DIMACS file
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
    
    def run_ursa(self, urs_code: str, debug_name: str = "") -> Tuple[str, float]:
        """
        Run URSA with a given URS code with timeout and memory limit.
        Python process stays alive even if URSA exceeds memory limit.
        """

        try:
            start_time = time.time()
            process = subprocess.Popen(
                [self.ursa_path, "-q", "-l32"], 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            try:
                stdout, stderr = process.communicate(input=urs_code, timeout=self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return "TIMEOUT", self.timeout

            end_time = time.time()
            actual_elapsed = end_time - start_time

            if process.returncode == 0:
                if is_sat_output(stdout):
                    return "SAT", actual_elapsed
                elif is_unsat_output(stdout):
                    return "UNSAT", actual_elapsed
                else:
                    return "UNKNOWN", actual_elapsed
            else:
                return "ERROR", actual_elapsed

        except Exception as e:
            print(f"URSA error: {e}")
            return "ERROR", 0.0

    def run_minisat(self, dimacs_file: str) -> Tuple[str, float]:
        """Run MiniSat on a DIMACS file and return (status, elapsed_time)."""
        try:
            start_time = time.time()
            
            process = subprocess.Popen(
                [self.minisat_path, dimacs_file, "/dev/null"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                return "TIMEOUT", self.timeout
                
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # MiniSat exit codes: 10=SAT, 20=UNSAT
            if process.returncode == 10:
                return "SAT", elapsed_time
            elif process.returncode == 20:
                return "UNSAT", elapsed_time
            else:
                return "ERROR", elapsed_time
                
        except Exception as e:
            print(f"MiniSat error: {e}")
            return "ERROR", 0.0
            
    def parse_and_generate(self, dimacs_file: str) -> Tuple[int, int, List[List[int]]]:
        """Read and parse a DIMACS file into (num_vars, num_clauses, clauses)."""
        with open(dimacs_file, "r") as f:
            dimacs_content = f.read()
        return self.parse_dimacs(dimacs_content)

    def run_with_template(self, num_vars: int, num_clauses: int, clauses: List[List[int]],
        template: str, save_dir: str = None, suffix: str = "",
        label: str = "URSA", verbose: bool = False, original_filename: str = None) -> Tuple[str, float]:
        """
        Generate URS code from DIMACS data, optionally save it, run URSA solver,
        and return (status, elapsed_time).
        """
        urs_code = self.generate_urs_code(num_vars, num_clauses, clauses, template)

        if save_dir and original_filename:
            filepath = self.save_urs_code(urs_code, original_filename, save_dir, suffix)
            if filepath and verbose:
                print(f"{label} code saved to: {filepath}")

        status, elapsed = self.run_ursa(urs_code, label if verbose else "")
        if verbose:
            print(f"{label}: {status} ({elapsed:.6f}s)")

        return status, elapsed
    
    def benchmark_file(self, dimacs_file: str, verbose: bool = True) -> Dict[str, any]:
        """Benchmark a single DIMACS file with URSA, MiniSat, and optionally URSA Reduction."""
        file_name = os.path.basename(dimacs_file)

        # Skip if already processed in continue mode
        if self.continue_mode and file_name in self.processed_files:
            if verbose:
                print(f"Skipping already processed: {file_name}")
            return None

        if verbose:
            print(f"Testing: {file_name}")

        # Parse DIMACS file
        try:
            num_vars, num_clauses, clauses = self.parse_and_generate(dimacs_file)
            if verbose:
                print(f"Parsed: {num_vars} variables, {num_clauses} clauses")
        except Exception as e:
            if verbose:
                print(f"Error parsing {dimacs_file}: {e}")
            return None

        # Run URSA
        ursa_status, ursa_time = self.run_with_template(
            num_vars, num_clauses, clauses,
            template=self.solver_template,
            save_dir=self.urs_output_dir if self.save_urs else None,
            label="URSA",
            verbose=verbose,
            original_filename=file_name
        )

        # Run MiniSat
        minisat_status, minisat_time = self.run_minisat(dimacs_file)
        if verbose:
            print(f"MiniSat: {minisat_status} ({minisat_time:.6f}s)")

        result = {
            "file": file_name,
            "variables": num_vars,
            "clauses": num_clauses,
            "ursa_status": ursa_status,
            "ursa_time": ursa_time,
            "minisat_status": minisat_status,
            "minisat_time": minisat_time,
        }

        # Run URSA Reduction if template provided
        if self.reduction_template:
            reduction_status, reduction_time = self.run_with_template(
                num_vars, num_clauses, clauses,
                template=self.reduction_template,
                save_dir=self.reduction_output_dir if self.save_urs else None,
                suffix="_reduction",
                label="Reduction",
                verbose=verbose,
                original_filename=file_name
            )
            result["reduction_status"] = reduction_status
            result["reduction_time"] = reduction_time

        return result


    def benchmark_directory(self, dimacs_dir: str, output_file: str = "SAT_benchmark_results.txt"):
        """Benchmark all .cnf files in a directory, with support for continue mode."""

        self.processed_files, self.existing_stats, self.existing_header = self.load_or_init_stats()

        dimacs_files = find_dimacs_files(dimacs_dir)
        print(f"Found {len(dimacs_files)} DIMACS files")

        files_to_process = filter_files(dimacs_files, self.processed_files, self.continue_mode)

        # fresh stats for this run
        stats = self._initialize_empty_stats()

        file_mode = prepare_output_file(output_file, self.continue_mode)

        # --- Processing ---
        with open(output_file, file_mode) as f:
            if file_mode == "w":
                solver_name = "solver_template"
                reduction_name = "reduction_template" if self.reduction_template else None
                write_header(f, solver_name, reduction_name, self.save_urs)

            for i, dimacs_file in enumerate(files_to_process, 1):
                # benchmark single file
                print(f"Testing: {os.path.basename(dimacs_file)}, {i}/{len(files_to_process)} ...", end="", flush=True)
                start_time = time.time()
                result = self.benchmark_file(dimacs_file, verbose=False)
                end_time = time.time()

                if result is None:
                    print(" (SKIPPED or FAILED)")
                    continue

                total_time = end_time - start_time
                print(f" ({total_time:.6f}s)")

                update_stats(stats, result, has_reduction=bool(self.reduction_template))
                category = extract_category(dimacs_file)

                line_parts = [
                    f"{category:<12}",
                    f"{result['file']:<35}",
                    f"{result['variables']:<9}",
                    f"{result['clauses']:<8}",
                    f"{result['ursa_status']:<8}",
                    f"{result['minisat_status']:<8}",
                ]

                if self.reduction_template:
                    line_parts.append(f"{result['reduction_status']:<10}")

                line_parts.extend([
                    f"{result['ursa_time']:<10.6f}",
                    f"{result['minisat_time']:<12.6f}"
                ])
                
                if self.reduction_template:
                    line_parts.append(f"{result['reduction_time']:<14.6f}")
                    
                
                f.write(" | ".join(line_parts) + "\n")
                f.flush()

            # merge and write stats
            combined_stats = {
                "total": self.existing_stats["total"] + stats["total"],
                "ursa": {k: self.existing_stats["ursa"][k] + stats["ursa"][k] for k in self.existing_stats["ursa"]},
                "minisat": {k: self.existing_stats["minisat"][k] + stats["minisat"][k] for k in self.existing_stats["minisat"]},
                "reduction": {k: self.existing_stats["reduction"][k] + stats["reduction"][k] for k in self.existing_stats["reduction"]},
            }
            write_final_statistics(f, combined_stats, has_reduction=bool(self.reduction_template))

        if self.continue_mode:
            print(f"Benchmark completed. Added {stats['total']} new results.")
            print(f"Total instances in {output_file}: {combined_stats['total']}")
        else:
            print(f"Benchmark completed. Results saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark SAT solvera: URSA vs MiniSat (opciono i Reduction template)"
    )
    parser.add_argument("dimacs_dir", nargs="?", help="Directory containing DIMACS .cnf files")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    parser.add_argument("--output", default="SAT_results.txt", help="Output file")
    parser.add_argument("--single-file", help="Test single DIMACS file instead of directory")
    parser.add_argument("--solver-template", required=True,
                        help="Path to file containing URS solver template (REQUIRED)")
    parser.add_argument("--reduction-template", help="Path to file containing URS reduction template (OPTIONAL)")
    parser.add_argument("--save-urs", action="store_true", help="Save generated URS code to files")
    parser.add_argument("--continue", dest="continue_mode", action="store_true",
                        help="Continue from previous run - skip already processed files and append new results")

    args = parser.parse_args()

    # Učitavanje solver template-a
    try:
        with open(args.solver_template, "r") as f:
            solver_template = f.read()
        print(f"Loaded solver template from: {args.solver_template}")
    except Exception as e:
        print(f"Error loading solver template {args.solver_template}: {e}")
        return

    # Učitavanje reduction template-a (opciono)
    reduction_template = None
    if args.reduction_template:
        try:
            with open(args.reduction_template, "r") as f:
                reduction_template = f.read()
            print(f"Loaded reduction template from: {args.reduction_template}")
        except Exception as e:
            print(f"Error loading reduction template {args.reduction_template}: {e}")
            return

    # Benchmark objekat (fiksirane putanje za URSA i MiniSat)
    benchmark = URSASATBenchmark(
        ursa_path="./ursa",
        minisat_path="minisat",
        timeout=args.timeout,
        solver_template=solver_template,
        reduction_template=reduction_template,
        save_urs=args.save_urs,
        urs_output_dir="SAT_saved_files",
        reduction_output_dir="SAT_reduction_saved_files",
        continue_mode=args.continue_mode,
        output_file=args.output,
    )

    # Pokretanje benchmark-a
    if args.single_file:
        # Single-file mod: samo ispis na konzolu (ne piše u output fajl)
        result = benchmark.benchmark_file(args.single_file, verbose=True)
        if result:
            if "urs_file" in result:
                print(f"URS file: {result['urs_file']}")
            if "reduction_file" in result:
                print(f"Reduction file: {result['reduction_file']}")
    else:
        if not args.dimacs_dir:
            print("Error: dimacs_dir is required when not using --single-file")
            return
        benchmark.benchmark_directory(args.dimacs_dir, args.output)


if __name__ == "__main__":
    main()
