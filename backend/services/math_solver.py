"""
Mathematical Problem Solver for Automated Math Solver
FOR TESTING PURPOSES ONLY

This module handles the core mathematical problem solving functionality:
- Text parsing and problem interpretation
- Symbolic mathematics using SymPy
- Numerical computations
- Step-by-step solution generation
- Error handling for unsolvable problems
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import traceback

import sympy as sp
import numpy as np
from sympy import symbols, solve, diff, integrate, limit, series, simplify
from sympy import Matrix, latex, pretty, sympify
from sympy.parsing.sympy_parser import parse_expr
from sympy.core.sympify import SympifyError
import matplotlib.pyplot as plt
from loguru import logger

from ..utils.validators import ContentValidator


class MathematicalSolver:
    """
    Core mathematical problem solver with comprehensive solving capabilities.
    
    Handles various types of mathematical problems including:
    - Algebraic equations and systems
    - Calculus (derivatives, integrals, limits)
    - Linear algebra (matrices, systems)
    - Trigonometry
    - Basic arithmetic and simplification
    """
    
    def __init__(self):
        """Initialize the mathematical solver."""
        self.validator = ContentValidator()
        self.solution_timeout = 300  # 5 minutes maximum per problem
        
        # Common mathematical symbols
        self.common_symbols = ['x', 'y', 'z', 't', 'a', 'b', 'c', 'n', 'k', 'm']
        
        # Problem type patterns
        self.problem_patterns = {
            'equation': r'(?:solve|find|calculate)\s+.*?[=]',
            'derivative': r'(?:derivative|differentiate|d/dx|∂/∂)',
            'integral': r'(?:integral|integrate|∫)',
            'limit': r'(?:limit|lim|approaches)',
            'matrix': r'(?:matrix|determinant|eigenvalue|system)',
            'simplify': r'(?:simplify|reduce|factor)',
            'graph': r'(?:graph|plot|sketch)',
            'optimization': r'(?:maximum|minimum|optimize|extrema)'
        }
    
    def solve_problem(self, problem_text: str, file_name: str = "") -> Dict[str, Any]:
        """
        Main method to solve a mathematical problem.
        
        Args:
            problem_text: The mathematical problem as text
            file_name: Name of the source file
            
        Returns:
            Dictionary containing solution information
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting to solve problem from: {file_name}")
            
            # Validate content first
            if not self._is_mathematical_problem(problem_text):
                return self._create_error_result(
                    "Content does not appear to be a mathematical problem",
                    problem_text, file_name, start_time
                )
            
            # Clean and preprocess the problem text
            cleaned_text = self._preprocess_text(problem_text)
            
            # Identify problem type
            problem_type = self._identify_problem_type(cleaned_text)
            logger.info(f"Identified problem type: {problem_type}")
            
            # Extract mathematical expressions
            expressions = self._extract_expressions(cleaned_text)
            
            if not expressions:
                return self._create_error_result(
                    "Could not extract mathematical expressions from the problem",
                    problem_text, file_name, start_time
                )
            
            # Solve based on problem type
            solution_result = self._solve_by_type(problem_type, expressions, cleaned_text)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create comprehensive result
            result = {
                'success': solution_result['success'],
                'problem_type': problem_type,
                'original_text': problem_text,
                'cleaned_text': cleaned_text,
                'expressions': expressions,
                'solution': solution_result.get('solution', ''),
                'steps': solution_result.get('steps', []),
                'latex_solution': solution_result.get('latex', ''),
                'numerical_result': solution_result.get('numerical', None),
                'graph_data': solution_result.get('graph', None),
                'error_message': solution_result.get('error', ''),
                'processing_time': f"{processing_time:.2f}s",
                'timestamp': datetime.now().isoformat(),
                'file_name': file_name
            }
            
            if result['success']:
                logger.info(f"Successfully solved problem in {processing_time:.2f}s")
            else:
                logger.warning(f"Failed to solve problem: {result['error_message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error solving problem: {e}")
            logger.error(traceback.format_exc())
            return self._create_error_result(
                f"Unexpected error: {str(e)}",
                problem_text, file_name, start_time
            )
    
    def _is_mathematical_problem(self, text: str) -> bool:
        """Check if text represents a mathematical problem."""
        # Use the validator to check mathematical content
        is_valid, _ = self.validator.validate_mathematical_content_text(text)
        return is_valid
    
    def _preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess the problem text.
        
        Args:
            text: Raw problem text
            
        Returns:
            Cleaned text ready for processing
        """
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Replace common mathematical symbols with standard notation
        replacements = {
            '×': '*',
            '÷': '/',
            '²': '^2',
            '³': '^3',
            '√': 'sqrt',
            '∞': 'oo',
            '≤': '<=',
            '≥': '>=',
            '≠': '!=',
            '±': '+/-',
            'π': 'pi',
            'α': 'alpha',
            'β': 'beta',
            'γ': 'gamma',
            'θ': 'theta',
            'λ': 'lambda',
            'μ': 'mu',
            'σ': 'sigma',
            'Δ': 'Delta',
            '∂': 'd'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _identify_problem_type(self, text: str) -> str:
        """
        Identify the type of mathematical problem.
        
        Args:
            text: Preprocessed problem text
            
        Returns:
            Problem type string
        """
        text_lower = text.lower()
        
        # Check patterns in order of specificity
        for problem_type, pattern in self.problem_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                return problem_type
        
        # Default classification based on content
        if '=' in text and any(var in text for var in self.common_symbols):
            return 'equation'
        elif any(op in text for op in ['+', '-', '*', '/', '^']):
            return 'simplify'
        else:
            return 'general'
    
    def _extract_expressions(self, text: str) -> List[str]:
        """
        Extract mathematical expressions from text.
        
        Args:
            text: Preprocessed problem text
            
        Returns:
            List of mathematical expressions
        """
        expressions = []
        
        # Remove common instruction words
        cleaned_text = re.sub(r'\b(solve|find|calculate|determine|compute|evaluate|simplify)\b', '', text, flags=re.IGNORECASE)
        cleaned_text = cleaned_text.strip()
        
        # Pattern for equations (most important)
        equation_pattern = r'([a-zA-Z][a-zA-Z0-9+\-*/^()\s]*=[\s]*[a-zA-Z0-9+\-*/^()\s]*)'
        equation_matches = re.findall(equation_pattern, cleaned_text)
        
        for match in equation_matches:
            cleaned = match.strip()
            if len(cleaned) > 2:
                expressions.append(cleaned)
        
        # If no equations found, try other patterns
        if not expressions:
            patterns = [
                r'\([a-zA-Z0-9+\-*/^().\s]+\)\([a-zA-Z0-9+\-*/^().\s]+\)',  # Products like (a+b)(a-b)
                r'[a-zA-Z0-9+\-*/^().\s]+(?:\^[0-9]+)?',  # General expressions
                r'\b\d+[a-zA-Z]\b',  # Coefficient notation like 2x
                r'[a-zA-Z]\([a-zA-Z0-9+\-*/^(),\s]+\)',  # Function notation
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, cleaned_text)
                for match in matches:
                    cleaned = match.strip()
                    if len(cleaned) > 2:
                        expressions.append(cleaned)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_expressions = []
        for expr in expressions:
            if expr not in seen:
                seen.add(expr)
                unique_expressions.append(expr)
        
        return unique_expressions
    
    def _is_valid_expression(self, expr: str) -> bool:
        """Check if string is a valid mathematical expression."""
        try:
            # Try to parse with SymPy
            parse_expr(expr, transformations='all')
            return True
        except (SympifyError, ValueError, TypeError):
            return False
    
    def _solve_by_type(self, problem_type: str, expressions: List[str], context: str) -> Dict[str, Any]:
        """
        Solve problem based on identified type.
        
        Args:
            problem_type: Type of mathematical problem
            expressions: List of mathematical expressions
            context: Full problem context
            
        Returns:
            Solution result dictionary
        """
        try:
            if problem_type == 'equation':
                return self._solve_equation(expressions, context)
            elif problem_type == 'derivative':
                return self._solve_derivative(expressions, context)
            elif problem_type == 'integral':
                return self._solve_integral(expressions, context)
            elif problem_type == 'limit':
                return self._solve_limit(expressions, context)
            elif problem_type == 'matrix':
                return self._solve_matrix(expressions, context)
            elif problem_type == 'simplify':
                return self._solve_simplify(expressions, context)
            elif problem_type == 'optimization':
                return self._solve_optimization(expressions, context)
            else:
                return self._solve_general(expressions, context)
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error solving {problem_type} problem: {str(e)}"
            }
    
    def _solve_equation(self, expressions: List[str], context: str) -> Dict[str, Any]:
        """Solve algebraic equations."""
        try:
            solutions = []
            steps = []
            
            for expr in expressions:
                if '=' in expr:
                    # Split equation
                    left, right = expr.split('=', 1)
                    
                    # Parse both sides
                    left_expr = parse_expr(left.strip())
                    right_expr = parse_expr(right.strip())
                    
                    # Create equation
                    equation = sp.Eq(left_expr, right_expr)
                    
                    # Find variables
                    variables = list(equation.free_symbols)
                    
                    if variables:
                        # Solve for each variable
                        for var in variables:
                            solution = solve(equation, var)
                            if solution:
                                solutions.append({
                                    'variable': str(var),
                                    'solutions': [str(sol) for sol in solution],
                                    'equation': str(equation)
                                })
                                steps.append(f"Solving for {var}: {solution}")
            
            if solutions:
                solution_text = self._format_equation_solutions(solutions)
                return {
                    'success': True,
                    'solution': solution_text,
                    'steps': steps,
                    'latex': self._generate_latex_solution(solutions),
                    'numerical': self._get_numerical_solutions(solutions)
                }
            else:
                return {
                    'success': False,
                    'error': "Could not find solutions to the equation(s)"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Equation solving error: {str(e)}"
            }
    
    def _solve_derivative(self, expressions: List[str], context: str) -> Dict[str, Any]:
        """Solve derivative problems."""
        try:
            results = []
            steps = []
            
            for expr in expressions:
                # Parse expression
                parsed_expr = parse_expr(expr)
                variables = list(parsed_expr.free_symbols)
                
                if variables:
                    for var in variables:
                        # Calculate derivative
                        derivative = diff(parsed_expr, var)
                        results.append({
                            'original': str(parsed_expr),
                            'variable': str(var),
                            'derivative': str(derivative)
                        })
                        steps.append(f"d/d{var}({parsed_expr}) = {derivative}")
            
            if results:
                solution_text = self._format_derivative_solutions(results)
                return {
                    'success': True,
                    'solution': solution_text,
                    'steps': steps,
                    'latex': self._generate_derivative_latex(results)
                }
            else:
                return {
                    'success': False,
                    'error': "Could not compute derivatives"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Derivative calculation error: {str(e)}"
            }
    
    def _solve_integral(self, expressions: List[str], context: str) -> Dict[str, Any]:
        """Solve integral problems."""
        try:
            results = []
            steps = []
            
            for expr in expressions:
                # Parse expression
                parsed_expr = parse_expr(expr)
                variables = list(parsed_expr.free_symbols)
                
                if variables:
                    for var in variables:
                        # Calculate integral
                        integral_result = integrate(parsed_expr, var)
                        results.append({
                            'original': str(parsed_expr),
                            'variable': str(var),
                            'integral': str(integral_result)
                        })
                        steps.append(f"∫{parsed_expr} d{var} = {integral_result}")
            
            if results:
                solution_text = self._format_integral_solutions(results)
                return {
                    'success': True,
                    'solution': solution_text,
                    'steps': steps,
                    'latex': self._generate_integral_latex(results)
                }
            else:
                return {
                    'success': False,
                    'error': "Could not compute integrals"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Integral calculation error: {str(e)}"
            }
    
    def _solve_simplify(self, expressions: List[str], context: str) -> Dict[str, Any]:
        """Simplify mathematical expressions."""
        try:
            results = []
            steps = []
            
            for expr in expressions:
                # Parse and simplify
                parsed_expr = parse_expr(expr)
                simplified = simplify(parsed_expr)
                
                results.append({
                    'original': str(parsed_expr),
                    'simplified': str(simplified)
                })
                steps.append(f"{parsed_expr} = {simplified}")
            
            if results:
                solution_text = self._format_simplify_solutions(results)
                return {
                    'success': True,
                    'solution': solution_text,
                    'steps': steps,
                    'latex': self._generate_simplify_latex(results)
                }
            else:
                return {
                    'success': False,
                    'error': "Could not simplify expressions"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Simplification error: {str(e)}"
            }
    
    def _solve_general(self, expressions: List[str], context: str) -> Dict[str, Any]:
        """Handle general mathematical problems."""
        try:
            # Try different approaches
            results = []
            steps = []
            
            for expr in expressions:
                parsed_expr = parse_expr(expr)
                
                # Try to evaluate numerically
                try:
                    numerical_value = float(parsed_expr.evalf())
                    results.append({
                        'expression': str(parsed_expr),
                        'value': numerical_value
                    })
                    steps.append(f"{parsed_expr} = {numerical_value}")
                except:
                    # Try to simplify
                    simplified = simplify(parsed_expr)
                    results.append({
                        'expression': str(parsed_expr),
                        'simplified': str(simplified)
                    })
                    steps.append(f"{parsed_expr} = {simplified}")
            
            if results:
                solution_text = "General solution:\n" + "\n".join(steps)
                return {
                    'success': True,
                    'solution': solution_text,
                    'steps': steps
                }
            else:
                return {
                    'success': False,
                    'error': "Could not solve the general problem"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"General solving error: {str(e)}"
            }
    
    def _create_error_result(self, error_message: str, original_text: str, 
                           file_name: str, start_time: float) -> Dict[str, Any]:
        """Create standardized error result."""
        processing_time = time.time() - start_time
        
        return {
            'success': False,
            'problem_type': 'unknown',
            'original_text': original_text,
            'solution': '',
            'steps': [],
            'error_message': error_message,
            'processing_time': f"{processing_time:.2f}s",
            'timestamp': datetime.now().isoformat(),
            'file_name': file_name
        }
    
    # Helper methods for formatting solutions
    def _format_equation_solutions(self, solutions: List[Dict]) -> str:
        """Format equation solutions for display."""
        formatted = "Equation Solutions:\n\n"
        for sol in solutions:
            formatted += f"For variable {sol['variable']}:\n"
            for s in sol['solutions']:
                formatted += f"  {sol['variable']} = {s}\n"
            formatted += "\n"
        return formatted
    
    def _format_derivative_solutions(self, results: List[Dict]) -> str:
        """Format derivative solutions for display."""
        formatted = "Derivative Solutions:\n\n"
        for result in results:
            formatted += f"d/d{result['variable']}({result['original']}) = {result['derivative']}\n"
        return formatted
    
    def _format_integral_solutions(self, results: List[Dict]) -> str:
        """Format integral solutions for display."""
        formatted = "Integral Solutions:\n\n"
        for result in results:
            formatted += f"∫{result['original']} d{result['variable']} = {result['integral']}\n"
        return formatted
    
    def _format_simplify_solutions(self, results: List[Dict]) -> str:
        """Format simplification results for display."""
        formatted = "Simplified Expressions:\n\n"
        for result in results:
            formatted += f"{result['original']} = {result['simplified']}\n"
        return formatted
    
    # Placeholder methods for additional functionality
    def _solve_limit(self, expressions: List[str], context: str) -> Dict[str, Any]:
        """Solve limit problems - placeholder implementation."""
        return {'success': False, 'error': 'Limit solving not yet implemented'}
    
    def _solve_matrix(self, expressions: List[str], context: str) -> Dict[str, Any]:
        """Solve matrix problems - placeholder implementation."""
        return {'success': False, 'error': 'Matrix solving not yet implemented'}
    
    def _solve_optimization(self, expressions: List[str], context: str) -> Dict[str, Any]:
        """Solve optimization problems - placeholder implementation."""
        return {'success': False, 'error': 'Optimization solving not yet implemented'}
    
    def _generate_latex_solution(self, solutions: List[Dict]) -> str:
        """Generate LaTeX representation of solutions."""
        return "LaTeX generation not yet implemented"
    
    def _generate_derivative_latex(self, results: List[Dict]) -> str:
        """Generate LaTeX for derivatives."""
        return "LaTeX generation not yet implemented"
    
    def _generate_integral_latex(self, results: List[Dict]) -> str:
        """Generate LaTeX for integrals."""
        return "LaTeX generation not yet implemented"
    
    def _generate_simplify_latex(self, results: List[Dict]) -> str:
        """Generate LaTeX for simplifications."""
        return "LaTeX generation not yet implemented"
    
    def _get_numerical_solutions(self, solutions: List[Dict]) -> List[float]:
        """Extract numerical values from solutions."""
        numerical = []
        for sol in solutions:
            for s in sol['solutions']:
                try:
                    numerical.append(float(s))
                except:
                    pass
        return numerical


# Add method to ContentValidator for text validation
def validate_mathematical_content_text(self, text: str) -> Tuple[bool, str]:
    """
    Validate mathematical content from text string.
    
    Args:
        text: Text content to validate
        
    Returns:
        Tuple of (is_valid, reason)
    """
    if not text or not text.strip():
        return False, "Empty or whitespace-only content"
    
    # Check for forbidden content
    if self._contains_forbidden_content(text):
        return False, "Text contains inappropriate content"
    
    # Check for mathematical content
    math_score = self._calculate_mathematical_score(text)
    
    if math_score < 0.1:  # Minimum 10% mathematical content
        return False, f"Insufficient mathematical content (score: {math_score:.2f})"
    
    return True, f"Valid mathematical content (score: {math_score:.2f})"

# Monkey patch the method to ContentValidator
ContentValidator.validate_mathematical_content_text = validate_mathematical_content_text
