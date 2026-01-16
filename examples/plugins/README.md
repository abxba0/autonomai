# Plugin System Quick Start

This is a quick reference for developers who want to create and use plugins for AutonomAI.

## Installation

The plugin system is part of the core AutonomAI package. No additional installation is required.

## Creating a Plugin

### 1. Validator Plugin

Create a validator that checks for specific patterns in outputs:

```python
from src.plugins import ValidatorPlugin, PluginMetadata, PluginConfig
from src.core.validator import BaseValidator, ValidationResult

class MyValidatorPlugin(ValidatorPlugin):
    @classmethod
    def get_metadata(cls):
        return PluginMetadata(
            name="my_validator",
            version="1.0.0",
            author="Your Name",
            description="Validates specific patterns",
            plugin_type="validator",
        )
    
    def create_validator(self):
        class MyValidator(BaseValidator):
            def validate(self, output, context=None):
                # Your validation logic
                is_valid = "required_text" in output
                return ValidationResult(
                    passed=is_valid,
                    validator_name=self.name,
                    error_message="Missing required text" if not is_valid else None
                )
        return MyValidator("my_validator")
```

### 2. Optimizer Plugin

Create an optimizer that analyzes failures and proposes fixes:

```python
from src.plugins import OptimizerPlugin, PluginMetadata
from src.models.config import FailureEntry
from src.models.critic_response import CriticResponse

class MyOptimizerPlugin(OptimizerPlugin):
    @classmethod
    def get_metadata(cls):
        return PluginMetadata(
            name="my_optimizer",
            version="1.0.0",
            author="Your Name",
            description="Custom failure optimizer",
            plugin_type="optimizer",
        )
    
    def can_handle(self, failure):
        # Check if this optimizer should handle the failure
        return "specific_pattern" in failure.failure_description
    
    def analyze_failure(self, failure, current_instructions, context=None):
        # Analyze and return proposed changes
        return CriticResponse(
            impact_analysis="Detailed analysis of the failure impact...",
            conflict_analysis="No conflicts detected with existing rules",
            safety_declaration=True,
            safety_reasoning="Safe to apply proposed changes because...",
            change_type="error_handling",
            proposed_appendix_update="## New Rule\n\nAdd specific handling...",
            confidence_score=0.8,
        )
```

### 3. Workflow Step Plugin

Create custom workflow step executors:

```python
from src.plugins import WorkflowStepPlugin, PluginMetadata
from src.models.workflow import WorkflowStep, StepStatus

class MyWorkflowStepPlugin(WorkflowStepPlugin):
    @classmethod
    def get_metadata(cls):
        return PluginMetadata(
            name="my_step_executor",
            version="1.0.0",
            author="Your Name",
            description="Custom step executor",
            plugin_type="workflow_step",
        )
    
    def can_execute(self, step):
        return hasattr(step, 'step_type') and step.step_type == "custom"
    
    def execute_step(self, step, context):
        try:
            # Your step execution logic
            result = "success"
            return StepStatus.COMPLETED, {"result": result}
        except Exception as e:
            return StepStatus.FAILED, {"error": str(e)}
```

## Using Plugins

### Method 1: Explicit Registration

```python
from src.plugins import PluginManager, PluginConfig

manager = PluginManager()

# Create plugin instance
plugin = MyValidatorPlugin(
    MyValidatorPlugin.get_metadata(),
    PluginConfig(enabled=True, priority=50)
)

# Register plugin
manager.register_plugin(plugin)
```

### Method 2: Directory Scanning

```python
from pathlib import Path

manager = PluginManager()
manager.discover_and_load_plugins(
    plugin_dirs=[Path("./plugins")]
)
```

### Method 3: Configuration File

Create `plugin_config.yaml`:

```yaml
plugins:
  - name: my_validator
    module: my_package.plugin
    class: MyValidatorPlugin
    config:
      enabled: true
      priority: 50
      settings:
        option1: value1
```

Load plugins:

```python
manager.discover_and_load_plugins(
    config_file=Path("./plugin_config.yaml")
)
```

### Method 4: Entry Points

In `setup.py`:

```python
setup(
    name="my-plugin-package",
    entry_points={
        "autonomai.plugins": [
            "my_plugin = my_package.plugin:MyPlugin",
        ],
    },
)
```

## Integrating with AutonomAI

### Add Validators to System

```python
from src import SelfOptimizingSystem
from src.plugins import PluginManager

system = SelfOptimizingSystem()
manager = PluginManager()

# Load plugins
manager.discover_and_load_plugins(plugin_dirs=[Path("./plugins")])

# Add plugin validators to system
for validator in manager.get_validators_for_pipeline():
    system.add_validator(validator)
```

### Use Optimizers for Failure Analysis

```python
# When a failure occurs
optimizer = manager.find_optimizer_for_failure(failure)
if optimizer:
    response = optimizer.analyze_failure(
        failure,
        current_instructions,
        context
    )
    # Apply the response...
```

### Use Workflow Step Executors

```python
# Find executor for a workflow step
executor = manager.find_workflow_step_executor(step)
if executor:
    status, outputs = executor.execute_step(step, context)
```

## Plugin Configuration

Configure plugin behavior with settings:

```python
config = PluginConfig(
    enabled=True,           # Enable/disable plugin
    priority=100,          # Lower = higher priority
    settings={             # Plugin-specific settings
        "threshold": 0.7,
        "max_retries": 3,
        "custom_option": "value"
    }
)

# Access settings in plugin
value = self.config.get("threshold", 0.5)
```

## Examples

See `examples/plugins/` for complete working examples:

- `keyword_validator_plugin.py` - Validator for required/forbidden keywords
- `failure_analyzer_plugin.py` - Pattern extraction from failures
- `workflow_step_plugin.py` - Custom workflow step executors

Run the demo:

```bash
python examples/plugin_system_demo.py
```

## Documentation

For complete documentation, see:

- [Plugin System Architecture](../docs/plugin-system.md) - Complete guide
- [API Reference](../docs/plugin-system.md#api-reference) - API documentation
- [Best Practices](../docs/plugin-system.md#best-practices) - Development guidelines

## Testing

Test your plugins:

```python
import pytest
from src.plugins import PluginManager

def test_my_plugin():
    manager = PluginManager()
    plugin = MyPlugin(MyPlugin.get_metadata())
    
    assert manager.register_plugin(plugin) is True
    assert plugin.lifecycle_state == PluginLifecycle.ACTIVE
    
    # Test plugin functionality
    # ...
```

Run tests:

```bash
python -m pytest tests/test_plugin_system.py -v
```

## Troubleshooting

### Plugin Not Loading

- Check that plugin class inherits from correct base class
- Verify `get_metadata()` is implemented
- Check plugin type matches expected values
- Look for errors in logs

### Import Errors

- Ensure all dependencies are installed
- Check Python path includes plugin directory
- Verify module and class names in config

### Plugin Not Executing

- Check plugin is enabled: `plugin.config.enabled`
- Verify plugin state: `plugin.lifecycle_state`
- Check priority if multiple plugins compete
- Review `can_handle()` or `can_execute()` logic

## Support

- GitHub Issues: Report bugs or request features
- Examples: See `examples/plugins/` directory
- Tests: See `tests/test_plugin_system.py` for usage patterns
