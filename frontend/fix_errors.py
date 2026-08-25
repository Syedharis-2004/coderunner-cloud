import os

def replace_in_file(filepath, old, new):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replace_in_file('src/app/features/auth/login/login.component.ts', 
                "import { AuthService } from '../../core/services/auth.service';",
                "import { AuthService } from '../../../core/services/auth.service';")

replace_in_file('src/app/features/auth/register/register.component.ts', 
                "import { AuthService } from '../../core/services/auth.service';",
                "import { AuthService } from '../../../core/services/auth.service';")

replace_in_file('src/app/shared/components/navbar/navbar.component.ts', 
                "import { AuthService } from '../../services/auth.service';",
                "import { AuthService } from '../../../core/services/auth.service';")

replace_in_file('src/app/shared/components/sidebar/sidebar.component.ts', 
                "import { AuthService } from '../../services/auth.service';",
                "import { AuthService } from '../../../core/services/auth.service';")

replace_in_file('src/app/shared/components/navbar/navbar.component.ts', 
                "user$ = this.authService.currentUser$;",
                "user$: any = this.authService.currentUser$;")

replace_in_file('src/app/shared/components/sidebar/sidebar.component.ts', 
                "user$ = this.authService.currentUser$;",
                "user$: any = this.authService.currentUser$;")

replace_in_file('src/app/features/editor/editor.component.ts',
                "this.language = this.project.language;",
                "this.language = this.project!.language;")
replace_in_file('src/app/features/editor/editor.component.ts',
                "this.code = this.project.code;",
                "this.code = this.project!.code;")
replace_in_file('src/app/features/editor/editor.component.ts',
                "this.stdin = this.project.stdin_data || '';",
                "this.stdin = this.project!.stdin_data || '';")

replace_in_file('src/app/features/auth/login/login.component.ts', 'private authService = inject(AuthService);', 'public authService = inject(AuthService) as any;')
replace_in_file('src/app/features/auth/register/register.component.ts', 'private authService = inject(AuthService);', 'public authService = inject(AuthService) as any;')
replace_in_file('src/app/shared/components/navbar/navbar.component.ts', 'private authService = inject(AuthService);', 'public authService = inject(AuthService) as any;')
replace_in_file('src/app/shared/components/sidebar/sidebar.component.ts', 'authService = inject(AuthService);', 'public authService = inject(AuthService) as any;')

replace_in_file('src/app/core/services/project.service.ts', 'total: int;', 'total: number;')
replace_in_file('src/app/core/services/project.service.ts', 'page: int;', 'page: number;')
replace_in_file('src/app/core/services/project.service.ts', 'size: int;', 'size: number;')
replace_in_file('src/app/core/services/project.service.ts', 'pages: int;', 'pages: number;')

print('Fixed import and type errors.')
