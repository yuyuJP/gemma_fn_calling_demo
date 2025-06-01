# Gemma 3 Function Calling Examples

This folder contains simple, focused examples that demonstrate Gemma 3's function calling capabilities without the complexity of MCP or advanced architectures.

## Examples

### 1. `basic_example.py` - Minimal Function Calling
**Perfect for beginners**

A bare-bones example showing the core concept:
- How to prompt Gemma 3 for function calling
- JSON extraction from model responses  
- Function execution and response handling
- 4 simple test cases

```bash
python examples/basic_example.py
```

**Key learning points:**
- The JSON format: `{"tool_call": {"name": "...", "arguments": {...}}}`
- System prompt design for function calling
- Two-step conversation: request → function call → final response

### 2. `simple_function_calling.py` - Interactive Demo
**More comprehensive example**

An interactive demo with:
- Multiple tool functions (time, calculator, weather)
- Retry loop for robust interaction
- Better error handling
- Interactive command-line interface

```bash
python examples/simple_function_calling.py
```

**Key learning points:**
- Tool registry pattern
- Robust JSON parsing with brace counting
- Conversation history management
- Error recovery strategies

## What You'll Learn

### Core Concepts
1. **Function Calling Format**: How Gemma 3 generates JSON tool calls
2. **Prompt Engineering**: Designing system prompts for function calling
3. **JSON Parsing**: Extracting structured data from model responses
4. **Conversation Flow**: Managing multi-turn interactions with tools

### Key Differences from OpenAI
- Gemma 3 uses JSON-in-text format instead of structured function calling
- Requires explicit prompt engineering for tool awareness
- Uses conversation history for context management
- Needs custom JSON parsing logic

## Quick Start

1. Make sure Ollama is running with Gemma 3:
   ```bash
   ollama run gemma3:12b
   ```

2. Run the basic example:
   ```bash
   python examples/basic_example.py
   ```

3. Try the interactive demo:
   ```bash
   python examples/simple_function_calling.py
   ```

## Sample Interactions

### Time Query
```
User: What time is it?
Gemma: {"tool_call": {"name": "get_time", "arguments": {}}}
Function result: Current time: 14:30:25
Final answer: The current time is 14:30:25.
```

### Math Calculation
```
User: What's 15 plus 27?
Gemma: {"tool_call": {"name": "add_numbers", "arguments": {"a": 15, "b": 27}}}
Function result: 15 + 27 = 42
Final answer: 15 plus 27 equals 42.
```

### No Function Call Needed
```
User: Hello, how are you?
Gemma: Hello! I'm doing well, thank you for asking. How can I help you today?
```

## Understanding the Code

### System Prompt Design
The system prompt is crucial for teaching Gemma 3 about available functions:
```python
SYSTEM_PROMPT = """You can call these functions:
1. get_time() - Returns current time
2. add_numbers(a, b) - Adds two numbers

To call a function, respond with JSON in this format:
{"tool_call": {"name": "function_name", "arguments": {"param": "value"}}}
```

### JSON Extraction
Gemma 3 generates JSON within natural language, so we need robust parsing:
```python
def extract_function_call(response: str):
    if '{"tool_call":' in response:
        # Find matching braces and extract JSON
```

### Function Execution
Simple registry pattern for executing functions:
```python
def execute_function(name: str, args: dict):
    if name == "get_time":
        return get_time()
    # ... handle other functions
```

## Next Steps

After understanding these examples:
1. Study the main MCP-based application in the `app/` directory
2. Read the article plots in `article_plots/` for deeper insights
3. Run the test suite to understand validation patterns
4. Experiment with your own function implementations

## Common Issues

### Model Not Responding
- Ensure Ollama is running: `ollama list`
- Check model availability: `ollama run gemma3:12b`

### JSON Parsing Errors
- The model sometimes generates malformed JSON
- The examples include robust parsing with error handling
- Consider retry logic for production use

### Function Call Format
- Gemma 3 is sensitive to the exact JSON format
- Include clear examples in your system prompt
- Test with various prompt phrasings for consistency