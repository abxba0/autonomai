"""
Example: Using the Plugin System

This example demonstrates how to use the AutonomAI plugin system
to load and use custom validators, optimizers, and workflow steps.
"""

from pathlib import Path
from src import SelfOptimizingSystem, SystemConfig
from src.plugins import PluginManager, PluginConfig
from src.core.validator import ValidationPipeline

# Import example plugins
import sys
sys.path.insert(0, str(Path(__file__).parent))

from plugins.keyword_validator_plugin import KeywordValidatorPlugin
from plugins.failure_analyzer_plugin import PatternAnalyzerPlugin
from plugins.workflow_step_plugin import DataTransformStepPlugin


def main():
    print("=" * 60)
    print("AutonomAI Plugin System Demo")
    print("=" * 60)
    print()
    
    # Initialize plugin manager
    print("1. Initializing Plugin Manager...")
    manager = PluginManager()
    print("   ✓ Plugin manager initialized")
    print()
    
    # Method 1: Register plugins explicitly
    print("2. Registering Plugins Explicitly...")
    
    # Register keyword validator
    keyword_config = PluginConfig(
        enabled=True,
        priority=50,
        settings={
            "required_keywords": ["analysis", "results"],
            "forbidden_keywords": ["error", "crash"],
        }
    )
    keyword_plugin = KeywordValidatorPlugin(
        KeywordValidatorPlugin.get_metadata(),
        keyword_config
    )
    
    if manager.register_plugin(keyword_plugin):
        print("   ✓ Keyword validator plugin registered")
    else:
        print("   ✗ Failed to register keyword validator")
    
    # Register pattern analyzer
    analyzer_plugin = PatternAnalyzerPlugin(
        PatternAnalyzerPlugin.get_metadata(),
        PluginConfig(enabled=True, priority=100)
    )
    
    if manager.register_plugin(analyzer_plugin):
        print("   ✓ Pattern analyzer plugin registered")
    else:
        print("   ✗ Failed to register pattern analyzer")
    
    # Register workflow step plugin
    workflow_plugin = DataTransformStepPlugin(
        DataTransformStepPlugin.get_metadata(),
        PluginConfig(enabled=True, priority=100)
    )
    
    if manager.register_plugin(workflow_plugin):
        print("   ✓ Workflow step plugin registered")
    else:
        print("   ✗ Failed to register workflow step plugin")
    
    print()
    
    # Method 2: Load from configuration file
    print("3. Loading from Configuration File...")
    try:
        config_file = Path(__file__).parent.parent / "plugin_config.yaml"
        if config_file.exists():
            results = manager.discover_and_load_plugins(
                config_file=config_file
            )
            print(f"   ✓ Loaded {len(results.get('config', []))} plugins from config")
        else:
            print("   ⓘ Config file not found (plugin_config.yaml)")
    except Exception as e:
        print(f"   ⚠ Warning: Could not load from config: {e}")
    
    print()
    
    # Method 3: Load from directory
    print("4. Discovering Plugins from Directory...")
    try:
        plugin_dir = Path(__file__).parent / "plugins"
        if plugin_dir.exists():
            results = manager.discover_and_load_plugins(
                plugin_dirs=[plugin_dir]
            )
            print(f"   ✓ Scanned plugins directory")
        else:
            print("   ⓘ Plugins directory not found")
    except Exception as e:
        print(f"   ⚠ Warning: Could not scan directory: {e}")
    
    print()
    
    # List all loaded plugins
    print("5. Loaded Plugins Summary:")
    print("-" * 60)
    plugins = manager.list_plugins()
    
    if plugins:
        for plugin in plugins:
            status_icon = "✓" if plugin["enabled"] else "○"
            print(f"   {status_icon} {plugin['name']} v{plugin['version']}")
            print(f"      Type: {plugin['type']}")
            print(f"      State: {plugin['state']}")
            print(f"      Priority: {plugin['priority']}")
            if plugin['error']:
                print(f"      Error: {plugin['error']}")
            print()
    else:
        print("   No plugins loaded")
    
    print()
    
    # Demonstrate validator integration
    print("6. Using Validator Plugins:")
    print("-" * 60)
    
    # Initialize system
    system = SelfOptimizingSystem(SystemConfig())
    
    # Add plugin validators to pipeline
    plugin_validators = manager.get_validators_for_pipeline()
    for validator in plugin_validators:
        system.validation_pipeline.add_validator(validator)
        print(f"   ✓ Added validator: {validator.name}")
    
    # Test validation
    print("\n   Testing validation with keyword plugin...")
    test_output = "Here are the analysis and results of the study."
    all_passed, results = system.validation_pipeline.validate(test_output)
    
    print(f"   Validation result: {'PASSED' if all_passed else 'FAILED'}")
    for result in results:
        status = "✓" if result.passed else "✗"
        print(f"      {status} {result.validator_name}: {result.error_message or 'OK'}")
    
    print()
    
    # Demonstrate optimizer integration
    print("7. Using Optimizer Plugins:")
    print("-" * 60)
    
    optimizers = manager.get_optimizer_plugins()
    print(f"   Available optimizers: {len(optimizers)}")
    for optimizer in optimizers:
        print(f"   - {optimizer.metadata.name}: {optimizer.metadata.description}")
    
    print()
    
    # Demonstrate workflow step integration
    print("8. Using Workflow Step Plugins:")
    print("-" * 60)
    
    workflow_plugins = manager.get_workflow_step_plugins()
    print(f"   Available workflow step plugins: {len(workflow_plugins)}")
    for plugin in workflow_plugins:
        print(f"   - {plugin.metadata.name}: {plugin.metadata.description}")
    
    # Test workflow step execution
    if workflow_plugins:
        from src.models.workflow import WorkflowStep, StepStatus
        
        print("\n   Testing workflow step execution...")
        test_step = WorkflowStep(
            name="demo_step",
            description="uppercase: Convert to uppercase",
        )
        test_step.step_type = "data_transform"
        test_step.inputs = {"data": "hello plugin world"}
        
        executor = manager.find_workflow_step_executor(test_step)
        if executor:
            print(f"   ✓ Found executor: {executor.metadata.name}")
            status, outputs = executor.execute_step(test_step, {})
            print(f"   Execution status: {status.value}")
            if status == StepStatus.COMPLETED:
                print(f"   Result: {outputs.get('transformed_data')}")
        else:
            print("   ✗ No executor found for step")
    
    print()
    
    # Plugin management
    print("9. Plugin Management:")
    print("-" * 60)
    
    if plugins:
        first_plugin = plugins[0]
        plugin_name = first_plugin["name"]
        
        print(f"   Demonstrating with plugin: {plugin_name}")
        
        # Disable plugin
        if manager.disable_plugin(plugin_name):
            print(f"   ✓ Disabled {plugin_name}")
        
        # Enable plugin
        if manager.enable_plugin(plugin_name):
            print(f"   ✓ Re-enabled {plugin_name}")
        
        print()
    
    # Summary
    print("=" * 60)
    print("Plugin System Demo Complete!")
    print("=" * 60)
    print()
    print("Key Takeaways:")
    print("- Plugins can be loaded from multiple sources")
    print("- Validators integrate seamlessly with ValidationPipeline")
    print("- Optimizers can be matched to specific failures")
    print("- Workflow steps can be extended with custom executors")
    print("- Plugin lifecycle is fully managed")
    print()
    print("See docs/plugin-system.md for full documentation")
    print()


if __name__ == "__main__":
    main()
