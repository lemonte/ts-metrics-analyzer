import os, lizard, traceback
from .language_map import get_language_by_extension, should_analyze_file

def process_commit(commit_obj):
    try:
        repo = commit_obj["repo"]
        commit = commit_obj["commit"]
        temp_dir = commit_obj["temp_dir"]
        missing_files = commit_obj.get("missing_files", {})
        repo.git.checkout(commit.hexsha)

        print(f"📍 Commit: {commit.hexsha} - {commit.message.strip()}")

        data = []
        
        # Handle initial commit (no parents) case
        if not commit.parents:
            print(f"Initial commit detected: {commit.hexsha}")
            # Get all files in the repository at this commit
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    # Skip .git directory and other non-analyzable files
                    if '.git' in root:
                        continue
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    
                    # Check if this file should be analyzed
                    if not should_analyze_file(file_path):
                        print(f"Skipping file: {rel_path} (not a supported file type)")
                        continue
                        
                    metrics = analyze_with_lizard(file_path)
                    if not metrics:
                        continue
                    
                    risco, qualidade, risk_comment, quality_comment = classify(metrics)
                    
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        try:
                            file_content = f.read()
                        except Exception as e:
                            print(f"Error reading file {file_path}: {e}")
                            file_content = "[Binary or unreadable file]"
                    
                    data.append({
                        "Autor": commit.author.name,
                        "SHA": commit.hexsha,
                        "Data": commit.committed_datetime.isoformat(),
                        "Mensagem": commit.message.strip(),

                        "Arquivo": rel_path,
                        "Código Alterado": file_content,
                        "Risco (Nível)": risco,
                        "Comentário Risco": risk_comment,
                        "Qualidade (Nível)": qualidade,
                        "Comentário Qualidade": quality_comment,
                        "metricas": metrics
                    })
            return data
            
        # Normal case with parent commits
        diff = commit.diff(commit.parents[0], create_patch=True)

        for d in diff:
            print(f"➡️ Encontrado diff em: {d.a_path}, tipo: {d.change_type}")
            path = d.b_path or d.a_path
            if not path:
                continue

            file_path = os.path.join(temp_dir, path)
            if not os.path.isfile(file_path):
                print(f"❌ Arquivo não existe: {file_path}")
                # Add to missing files tracking
                data.append({
                    "Autor": commit.author.name,
                    "SHA": commit.hexsha,
                    "Data": commit.committed_datetime.isoformat(),
                    "Mensagem": commit.message.strip(),
                    "Arquivo": path,
                    "error": "file_not_found"
                })
                missing_files[path] = True
                continue
                
            # Check if this file should be analyzed
            if not should_analyze_file(file_path):
                print(f"Skipping file: {path} (not a supported file type)")
                data.append({
                    "Autor": commit.author.name,
                    "SHA": commit.hexsha,
                    "Data": commit.committed_datetime.isoformat(),
                    "Mensagem": commit.message.strip(),
                    "Arquivo": path,
                    "error": "unsupported_file_type"
                })
                continue
                
            try:
                metrics = analyze_with_lizard(file_path)
                if not metrics:
                    continue

                risco, qualidade, risk_comment, quality_comment = classify(metrics)
                
                try:
                    diff_content = d.diff.decode("utf-8", errors="replace")
                except Exception as e:
                    print(f"Error decoding diff: {e}")
                    diff_content = "[Binary or unreadable diff]"

                # Get language from file extension
                ext = os.path.splitext(path)[1].lower()
                language = get_language_by_extension(ext)

                data.append({
                    "Autor": commit.author.name,
                    "SHA": commit.hexsha,
                    "Data": commit.committed_datetime.isoformat(),
                    "Mensagem": commit.message.strip(),
                    "Arquivo": path,
                    "Código Alterado": diff_content,
                    "Risco (Nível)": risco,
                    "Comentário Risco": risk_comment,
                    "Qualidade (Nível)": qualidade,
                    "Comentário Qualidade": quality_comment,
                    "metricas": metrics,
                    "language": language
                })
            except Exception as e:
                print(f"Error analyzing file {file_path}: {str(e)}")
                traceback.print_exc()
                
                # Add error information to results
                data.append({
                    "Autor": commit.author.name,
                    "SHA": commit.hexsha,
                    "Data": commit.committed_datetime.isoformat(),
                    "Mensagem": commit.message.strip(),
                    "Arquivo": path,
                    "error": "analysis_error",
                    "error_message": str(e)
                })
        return data
    except Exception as e:
        print(f"Error processing commit {commit_obj.get('commit', 'unknown')}: {str(e)}")
        traceback.print_exc()
        return []
def analyze_with_lizard(file_path):
    ext = os.path.splitext(file_path)[1]
    language = get_language_by_extension(ext)
    if not language:
        print(f"❌ Linguagem não suportada: {file_path}")
        return None
    
    try:
        # Read the file content for additional analysis
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
            
        # Use lizard for the primary analysis
        results = lizard.analyze_file(file_path)
        funcs = results.function_list
        
        # Count actual lines of code (excluding blank lines and comments)
        lines = [line.strip() for line in file_content.split('\n')]
        actual_loc = len([line for line in lines if line and not line.startswith('//') and not line.startswith('/*') and not line.startswith('#')])
        
        # Use regex to count loops more accurately for all languages
        import re
        
        # Common loop patterns across languages
        loop_patterns = [
            r'\bfor\s*\(',      # for loops: for (...
            r'\bwhile\s*\(',    # while loops: while (...
            r'\bdo\s*\{',       # do-while loops: do {...
            r'\bforeach\s*\(',  # foreach loops: foreach (...
            r'\.(forEach|map|filter|reduce|some|every)\s*\('  # JS/TS array methods
        ]
        
        # Count all loop types
        loop_count = sum(len(re.findall(pattern, file_content)) for pattern in loop_patterns)
        
        # Calculate nesting level by indentation (works for most languages)
        indent_levels = []
        for line in lines:
            if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('/*') and not line.strip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                indent_levels.append(indent // 2)  # Assuming 2 spaces per indent level
        
        max_nesting_level = max(indent_levels) if indent_levels else 0
        
        # Count return statements (common in most languages)
        return_count = len(re.findall(r'\breturn\b', file_content))
        
        # Function count from lizard
        function_count = len(funcs)
        
        # Try to get more accurate metrics from lizard if available
        try:
            if funcs:
                # Get cyclomatic complexity
                cc_sum = sum(f.cyclomatic_complexity for f in funcs)
                
                # Try to get max nesting from lizard if available
                if hasattr(funcs[0], 'max_nesting'):
                    lizard_max_nesting = max((f.max_nesting for f in funcs), default=0)
                    max_nesting_level = max(max_nesting_level, lizard_max_nesting)  # Use the higher value
        except (IndexError, AttributeError) as e:
            print(f"⚠️ Warning: Could not calculate some metrics from lizard for {file_path}: {e}")
            cc_sum = 0
    
    except Exception as e:
        print(f"⚠️ Erro ao analisar {file_path}: {e}")
        return None

    # Common patterns for various metrics (language-agnostic where possible)
    comparison_patterns = [r'\bif\b', r'\belse\b', r'\bswitch\b', r'==', r'!=', r'>=', r'<=', r'>', r'<']
    comparisons_count = sum(len(re.findall(pattern, file_content)) for pattern in comparison_patterns)
    
    try_catch_count = len(re.findall(r'\btry\b', file_content))
    parentheses_count = file_content.count('(')
    string_literals_count = len(re.findall(r'["\']', file_content)) // 2  # Divide by 2 for opening/closing quotes
    numbers_count = len(re.findall(r'\b\d+\b', file_content))
    assignment_count = len(re.findall(r'[^=!<>]=[^=]', file_content))  # = not preceded by =!<> and not followed by =
    
    # Math operations
    math_ops = ['+', '-', '*', '/', '%']
    math_ops_count = sum(file_content.count(op) for op in math_ops)
    
    # Variable declarations (common patterns)
    var_patterns = [r'\bvar\b', r'\blet\b', r'\bconst\b', r'\bint\b', r'\bfloat\b', r'\bdouble\b', r'\bstring\b', r'\bbool\b']
    variables_count = sum(len(re.findall(pattern, file_content)) for pattern in var_patterns)

    # Return the metrics
    return {
        "loc": actual_loc,
        "cbo": 0,  # Coupling between objects - not easily calculated
        "wmc": function_count,  # Weighted methods per class
        "dit": 0,  # Depth of inheritance tree - not easily calculated
        "rfc": cc_sum if 'cc_sum' in locals() else return_count,  # Response for class - approximated by cyclomatic complexity or return count
        "lcom": 0,  # Lack of cohesion of methods - not easily calculated
        "totalMethods": function_count,
        "totalFields": 0,  # Not easily calculated
        "nosi": 0,  # Number of static invocations - not easily calculated
        "returnQty": return_count,
        "loopQty": loop_count,
        "comparisonsQty": comparisons_count,
        "tryCatchQty": try_catch_count,
        "parenthesizedExpsQty": parentheses_count,
        "stringLiteralsQty": string_literals_count,
        "numbersQty": numbers_count,
        "assignmentsQty": assignment_count,
        "mathOperationsQty": math_ops_count,
        "variablesQty": variables_count,
        "maxNestedBlocks": max_nesting_level,
        "uniqueWordsQty": len(set(file_content.split()))
    }

def classify(metrics):
    # Define the metrics we'll evaluate and their thresholds
    metrics_to_evaluate = [
        # Metric name, threshold, is_higher_better
        ('loc', 150, False),  # Lines of code - lower is better
        ('wmc', 8, False),    # Weighted methods per class - lower is better
        ('rfc', 15, False),   # Response for class - lower is better
        ('maxNestedBlocks', 3, False),  # Max nesting - lower is better
        ('loopQty', 5, False),  # Loop quantity - lower is better
        ('comparisonsQty', 20, False),  # Comparisons - lower is better
        ('tryCatchQty', 3, False),  # Try-catch blocks - lower is better
        ('variablesQty', -1, True)  # Variables - evaluated differently
    ]
    
    # Risk assessment (negative points)
    risk_points = []
    
    # Quality assessment (positive points)
    quality_points = []
    
    # Evaluate each metric
    for metric_name, threshold, is_higher_better in metrics_to_evaluate:
        value = metrics.get(metric_name, 0)
        
        # Special case for variables - we want a reasonable ratio to LOC
        if metric_name == 'variablesQty':
            loc = metrics.get('loc', 1)  # Avoid division by zero
            ratio = value / loc if loc > 0 else 0
            
            if value > 0 and ratio <= 0.1:  # Good: Has variables but not too many
                quality_points.append(f"Uso eficiente de variáveis ({value})")
            elif value > 0 and ratio > 0.2:  # Bad: Too many variables
                risk_points.append(f"Muitas variáveis em relação ao tamanho do arquivo ({value})")
            continue
        
        # For all other metrics
        if is_higher_better:
            if value > threshold:
                quality_points.append(f"{metric_name_to_portuguese(metric_name, value, True)}")
            else:
                risk_points.append(f"{metric_name_to_portuguese(metric_name, value, False)}")
        else:  # Lower is better
            if value <= threshold:
                quality_points.append(f"{metric_name_to_portuguese(metric_name, value, True)}")
            else:
                risk_points.append(f"{metric_name_to_portuguese(metric_name, value, False)}")
    
    # Calculate overall scores
    risco = len(risk_points)
    qualidade = len(quality_points)
    
    # Generate comments
    risk_comment = "Código apresenta baixo risco operacional."
    if risk_points:
        risk_comment = f"Código com pontos de atenção: {', '.join(risk_points)}"
    
    quality_comment = "Código bem organizado e legível."
    if quality_points:
        quality_comment = f"Pontos positivos: {', '.join(quality_points)}"
    
    return risco, qualidade, risk_comment, quality_comment

def metric_name_to_portuguese(metric_name, value, is_positive):
    """Convert metric names to readable Portuguese descriptions"""
    if metric_name == 'loc':
        return f"Tamanho {'adequado' if is_positive else 'excessivo'} de arquivo (LOC: {value})"
    elif metric_name == 'wmc':
        return f"{'Boa' if is_positive else 'Má'} distribuição de métodos/funções ({value})"
    elif metric_name == 'rfc':
        return f"{'Baixa' if is_positive else 'Alta'} complexidade (RFC: {value})"
    elif metric_name == 'maxNestedBlocks':
        return f"Estrutura de código {'bem organizada' if is_positive else 'muito aninhada'} (profundidade: {value})"
    elif metric_name == 'loopQty':
        return f"{'Uso moderado' if is_positive else 'Excesso'} de loops ({value})"
    elif metric_name == 'comparisonsQty':
        return f"{'Quantidade adequada' if is_positive else 'Excesso'} de condições/comparações ({value})"
    elif metric_name == 'tryCatchQty':
        return f"{'Uso adequado' if is_positive else 'Excesso'} de blocos try-catch ({value})"
    else:
        return f"{metric_name}: {value}"
