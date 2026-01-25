#!/usr/bin/env python3
import os
import re
import sys


RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def get_project_name():
    """Get the project name from pubspec.yaml using regex"""
    if os.path.isfile("pubspec.yaml"):
        with open("pubspec.yaml", 'r') as file:
            try:
                content = file.read()
                # Use regex to find the name field in pubspec.yaml
                name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
                if name_match:
                    project_name = name_match.group(1).strip()
                    # Remove quotes if present
                    project_name = project_name.strip('"\'')
                    return project_name
                else:
                    print(f"{RED}Error: Could not find 'name' field in pubspec.yaml.{NC}")
                    exit(1)
            except Exception as e:
                print(f"{RED}Error: Could not read pubspec.yaml: {e}{NC}")
                exit(1)
    else:
        print(f"{RED}Error: pubspec.yaml not found in the current directory.{NC}")
        print(f"{YELLOW}Please run this command from the root of a Flutter project.{NC}")
        exit(1)

def update_service_locator(project_name, class_prefix, page_name):
    """Update service_locator.dart with the new feature DI"""
    service_locator_path = "lib/core/di/service_locator.dart"
    
    if not os.path.isfile(service_locator_path):
        print(f"{YELLOW}Warning: Could not find service_locator.dart at {service_locator_path}.{NC}")
        print(f"{YELLOW}Feature DI registration in service locator skipped.{NC}")
        return
    
    with open(service_locator_path, 'r') as file:
        content = file.read()
    
    # Add import statement
    import_statement = f"import 'package:{project_name}/features/{page_name}/di/{page_name}_di.dart';"
    if import_statement not in content:
        # Find the last import statement and add after it
        import_matches = re.findall(r'import [^;]+;', content)
        if import_matches:
            last_import = import_matches[-1]
            content = content.replace(last_import, f"{last_import}\n{import_statement}")
    
    # Add DI setup call in setUp method
    di_call = f"    await {class_prefix}Di.setup(_serviceLocator);"
    
    # Find the feature DI setup comment and add after it
    feature_comment_pattern = r'//Feature DI setup'
    if feature_comment_pattern in content:
        content = re.sub(
            r'(//Feature DI setup\s*\n)',
            f'\\1{di_call}\n',
            content
        )
    else:
        # If comment doesn't exist, add before the closing brace of setUp method
        setup_pattern = r'(\s+await\s+\w+\.setup\(_serviceLocator\);\s*\n)(\s*})'
        match = re.search(setup_pattern, content)
        if match:
            content = re.sub(
                setup_pattern,
                f'\\1\n    //Feature DI setup\n{di_call}\n\\2',
                content
            )
    
    with open(service_locator_path, 'w') as file:
        file.write(content)
    
    print(f"{GREEN}✓ Updated service_locator.dart with {class_prefix}Di registration.{NC}")
    print(f"{BLUE}  Added: {NC}{di_call}")

def generate_page(page_name):
    """Generate Flutter feature structure and files"""
    if not page_name:
        print(f"{RED}Error: Page name is required.{NC}")
        print(f"{BLUE}Usage: {sys.argv[0]} page <page_name>{NC}")
        exit(1)
    
    project_name = get_project_name()
    
    # Convert page name to lowercase
    page_name = page_name.lower()
    
    # Create class prefix - convert snake_case to PascalCase
    class_prefix = ''.join(word.capitalize() for word in page_name.split('_'))
    
    print(f"{YELLOW}Creating feature structure for {class_prefix} in {project_name} project...{NC}\n")
    
    # Create folder structure
    base_path = f"lib/features/{page_name}"
    os.makedirs(f"{base_path}/data/datasource", exist_ok=True)
    os.makedirs(f"{base_path}/data/models", exist_ok=True)
    os.makedirs(f"{base_path}/data/repositories", exist_ok=True)
    os.makedirs(f"{base_path}/domain/datasource", exist_ok=True)
    os.makedirs(f"{base_path}/domain/repositories", exist_ok=True)
    os.makedirs(f"{base_path}/domain/entities", exist_ok=True)
    os.makedirs(f"{base_path}/domain/usecase", exist_ok=True)
    os.makedirs(f"{base_path}/presentation/presenter", exist_ok=True)
    os.makedirs(f"{base_path}/presentation/ui", exist_ok=True)
    os.makedirs(f"{base_path}/presentation/widgets", exist_ok=True)
    os.makedirs(f"{base_path}/di", exist_ok=True)
    
    # Generate Domain Repository content
    domain_repository_content = f'''abstract class {class_prefix}Repository {{
  
}}
'''
    
    # Generate Data Repository Implementation content
    data_repository_content = f'''import 'package:{project_name}/features/{page_name}/domain/repositories/{page_name}_repository.dart';

class {class_prefix}RepositoryImpl implements {class_prefix}Repository {{
  
}}
'''
    
    # Generate DI file content
    di_content = f'''import 'package:{project_name}/core/base/base_presenter.dart';
import 'package:{project_name}/features/{page_name}/data/repositories/{page_name}_repository_impl.dart';
import 'package:{project_name}/features/{page_name}/domain/repositories/{page_name}_repository.dart';
import 'package:{project_name}/features/{page_name}/presentation/presenter/{page_name}_presenter.dart';

import 'package:get_it/get_it.dart';

class {class_prefix}Di {{
  static Future<void> setup(GetIt serviceLocator) async {{
    //  Data Source

    //  Repository
    serviceLocator.registerLazySingleton<{class_prefix}Repository>(
      () => {class_prefix}RepositoryImpl(),
    );

    // Use Cases

    // Presenters
    serviceLocator.registerFactory(
      () => loadPresenter({class_prefix}Presenter()),
    );
  }}
}}
'''

    # Generate presenter content
    presenter_content = f'''import 'dart:async';
import 'package:{project_name}/core/base/base_presenter.dart';
import 'package:{project_name}/core/utility/navigation_helpers.dart';
import 'package:{project_name}/features/{page_name}/presentation/presenter/{page_name}_ui_state.dart';

class {class_prefix}Presenter extends BasePresenter<{class_prefix}UiState> {{
  final Obs<{class_prefix}UiState> uiState = Obs<{class_prefix}UiState>({class_prefix}UiState.empty());
  {class_prefix}UiState get currentUiState => uiState.value;

  @override
  Future<void> addUserMessage(String message) async {{
    uiState.value = currentUiState.copyWith(userMessage: message);
    showMessage(message: currentUiState.userMessage);
  }}

  @override
  Future<void> toggleLoading({{required bool loading}}) async {{
    uiState.value = currentUiState.copyWith(isLoading: loading);
  }}
}}
'''
    
    # Generate UI state content
    ui_state_content = f'''import 'package:{project_name}/core/base/base_ui_state.dart';

class {class_prefix}UiState extends BaseUiState {{
  const {class_prefix}UiState({{required super.isLoading, required super.userMessage}});

  factory {class_prefix}UiState.empty() {{
    return {class_prefix}UiState(isLoading: false, userMessage: '');
  }}

  @override
  List<Object?> get props => [isLoading, userMessage];

  //Add more properties to the state

  {class_prefix}UiState copyWith({{bool? isLoading, String? userMessage}}) {{
    return {class_prefix}UiState(
      isLoading: isLoading ?? this.isLoading,
      userMessage: userMessage ?? this.userMessage,
    );
  }}
}}
'''
    
    # Generate page content
    page_content = f'''import 'package:flutter/material.dart';

class {class_prefix}Page extends StatelessWidget {{
  const {class_prefix}Page({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: Text('{class_prefix}')),
      body: Center(child: Text('{class_prefix}')),
    );
  }}
}}
'''
    
    # Write files
    with open(f"{base_path}/domain/repositories/{page_name}_repository.dart", 'w') as file:
        file.write(domain_repository_content)
    
    with open(f"{base_path}/data/repositories/{page_name}_repository_impl.dart", 'w') as file:
        file.write(data_repository_content)
    
    with open(f"{base_path}/di/{page_name}_di.dart", 'w') as file:
        file.write(di_content)
    
    with open(f"{base_path}/presentation/presenter/{page_name}_presenter.dart", 'w') as file:
        file.write(presenter_content)
    
    with open(f"{base_path}/presentation/presenter/{page_name}_ui_state.dart", 'w') as file:
        file.write(ui_state_content)
    
    with open(f"{base_path}/presentation/ui/{page_name}_page.dart", 'w') as file:
        file.write(page_content)
    
    # Update service locator
    update_service_locator(project_name, class_prefix, page_name)
    
    # Print success message
    print(f"\n{GREEN}✓ Feature '{class_prefix}' created successfully!{NC}")
    print(f"  {BLUE}Structure:{NC}")
    print(f"    └── {BLUE}lib/features/{page_name}{NC}")
    print(f"        ├── {BLUE}data{NC}")
    print(f"        │   ├── {BLUE}datasource{NC}")
    print(f"        │   └── {BLUE}repositories{NC}")
    print(f"        │       └── {GREEN}{page_name}_repository_impl.dart{NC}")
    print(f"        ├── {BLUE}domain{NC}")
    print(f"        │   ├── {BLUE}datasource{NC}")
    print(f"        │   ├── {BLUE}repositories{NC}")
    print(f"        │   │   └── {GREEN}{page_name}_repository.dart{NC}")
    print(f"        │   ├── {BLUE}entities{NC}")
    print(f"        │   └── {BLUE}usecase{NC}")
    print(f"        ├── {BLUE}presentation{NC}")
    print(f"        │   ├── {BLUE}presenter{NC}")
    print(f"        │   │   ├── {GREEN}{page_name}_presenter.dart{NC}")
    print(f"        │   │   └── {GREEN}{page_name}_ui_state.dart{NC}")
    print(f"        │   ├── {BLUE}ui{NC}")
    print(f"        │   │   └── {GREEN}{page_name}_page.dart{NC}")
    print(f"        │   └── {BLUE}widgets{NC}")
    print(f"        └── {BLUE}di{NC}")
    print(f"            └── {GREEN}{page_name}_di.dart{NC}")

def main():
    if len(sys.argv) < 3:
        print(f"{RED}Error: Insufficient arguments.{NC}")
        print(f"{BLUE}Usage: {sys.argv[0]} page <page_name>{NC}")
        exit(1)

    command = sys.argv[1].lower()

    if command == "page":
        if len(sys.argv) >= 3:
            generate_page(sys.argv[2])
        else:
            print(f"{RED}Error: Page name is required.{NC}")
            print(f"{BLUE}Usage: {sys.argv[0]} page <page_name>{NC}")
            exit(1)
    else:
        print(f"{RED}Error: Unknown command '{command}'.{NC}")
        print(f"{BLUE}Available commands: page{NC}")
        exit(1)

if __name__ == "__main__":
    main()