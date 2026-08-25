import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ExecutionService, ExecutionResult } from '../../core/services/execution.service';
import { ProjectService, ProjectDetail } from '../../core/services/project.service';

@Component({
  selector: 'app-editor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="editor-workspace">
      <div class="editor-header">
        <h2 class="cyber-title" style="font-size: 1.2rem; margin: 0;">
          {{ project?.name || 'NEW_PROJECT' }}
        </h2>
        
        <div class="actions">
          <select [(ngModel)]="language" class="cyber-select mr-2">
            <option value="python">PYTHON (3.11)</option>
            <option value="nodejs">NODE.JS (20.x)</option>
            <option value="go">GOLANG (1.21)</option>
            <option value="c">C (GCC)</option>
          </select>
          <button class="btn-cyber-solid" (click)="runCode()" [disabled]="isRunning">
            {{ isRunning ? 'EXECUTING...' : 'RUN_CODE' }}
          </button>
        </div>
      </div>

      <div class="workspace-split">
        <div class="code-area">
          <div class="area-label">CODE_BUFFER</div>
          <textarea 
            [(ngModel)]="code" 
            class="cyber-textarea" 
            placeholder="// Enter your code here..."
            spellcheck="false"
          ></textarea>
        </div>
        
        <div class="terminal-area">
          <div class="area-label">STDIN_BUFFER</div>
          <textarea 
            [(ngModel)]="stdin" 
            class="cyber-textarea stdin-textarea" 
            placeholder="Input data..."
            spellcheck="false"
          ></textarea>

          <div class="area-label mt-2">SYSTEM_OUTPUT</div>
          <div class="output-console" [class.error]="lastResult?.status === 'FAILED' || lastResult?.status === 'TIMEOUT'">
            <div *ngIf="!lastResult && !isRunning" class="placeholder-text">WAITING_FOR_EXECUTION...</div>
            <div *ngIf="isRunning" class="loading-text">PROCESSING... <span class="blink">_</span></div>
            
            <ng-container *ngIf="lastResult">
              <div class="meta-info">
                STATUS: [{{ lastResult.status }}] | EXIT_CODE: [{{ lastResult.exit_code }}] | TIME: [{{ lastResult.execution_time | number:'1.0-3' }}s]
              </div>
              <pre *ngIf="lastResult.stdout" class="stdout">{{ lastResult.stdout }}</pre>
              <pre *ngIf="lastResult.stderr" class="stderr">{{ lastResult.stderr }}</pre>
            </ng-container>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .editor-workspace {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 112px); /* 100vh - navbar(64) - padding(48) */
    }
    .editor-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding: 12px 16px;
      background: var(--cyber-surface);
      border: 1px solid var(--cyber-surface-border);
      border-radius: 4px;
    }
    .actions {
      display: flex;
      align-items: center;
    }
    .cyber-select {
      background: #000;
      color: var(--cyber-neon);
      border: 1px solid var(--cyber-neon);
      padding: 8px 12px;
      font-family: var(--font-family-mono);
      outline: none;
    }
    .mr-2 { margin-right: 16px; }
    .mt-2 { margin-top: 16px; }
    
    .workspace-split {
      display: flex;
      gap: 16px;
      flex: 1;
      overflow: hidden;
    }
    .code-area {
      flex: 2;
      display: flex;
      flex-direction: column;
    }
    .terminal-area {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    .area-label {
      font-family: var(--font-family-mono);
      font-size: 0.75rem;
      color: var(--cyber-text-dim);
      margin-bottom: 4px;
      background: var(--cyber-surface);
      padding: 4px 8px;
      border: 1px solid var(--cyber-surface-border);
      border-bottom: none;
      display: inline-block;
      align-self: flex-start;
    }
    .cyber-textarea {
      flex: 1;
      width: 100%;
      background: #000;
      color: #fff;
      font-family: var(--font-family-mono);
      font-size: 14px;
      border: 1px solid var(--cyber-surface-border);
      padding: 16px;
      resize: none;
      outline: none;
    }
    .cyber-textarea:focus {
      border-color: var(--cyber-neon);
      box-shadow: inset 0 0 10px rgba(0,255,0,0.1);
    }
    .stdin-textarea {
      flex: none;
      height: 100px;
    }
    .output-console {
      flex: 1;
      background: #050505;
      border: 1px solid var(--cyber-surface-border);
      padding: 16px;
      font-family: var(--font-family-mono);
      font-size: 14px;
      overflow-y: auto;
      color: var(--cyber-text);
    }
    .output-console.error {
      border-color: var(--cyber-accent-danger);
    }
    .placeholder-text {
      color: var(--cyber-text-dim);
      opacity: 0.5;
    }
    .loading-text {
      color: var(--cyber-neon);
    }
    .blink {
      animation: blink 1s step-end infinite;
    }
    @keyframes blink { 50% { opacity: 0; } }
    
    .meta-info {
      font-size: 0.8rem;
      color: var(--cyber-text-dim);
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px dashed var(--cyber-surface-border);
    }
    .stdout {
      margin: 0;
      white-space: pre-wrap;
      color: var(--cyber-text);
    }
    .stderr {
      margin: 0;
      white-space: pre-wrap;
      color: var(--cyber-accent-danger);
    }
  `]
})
export class EditorComponent implements OnInit {
  executionService = inject(ExecutionService);
  projectService = inject(ProjectService);
  route = inject(ActivatedRoute);

  projectId: string | null = null;
  project: ProjectDetail | null = null;
  
  language = 'python';
  code = 'print("Hello, CodeRunner Cloud!")';
  stdin = '';
  
  isRunning = false;
  lastResult: ExecutionResult | null = null;

  ngOnInit() {
    this.projectId = this.route.snapshot.paramMap.get('id');
    if (this.projectId) {
      this.loadProject(this.projectId);
    }
  }

  loadProject(id: string) {
    this.projectService.getProject(id).subscribe((res: any) => {
      if (res.success && res.data) {
        this.project = res.data;
        this.language = this.project!.language;
        this.code = this.project!.code;
        this.stdin = this.project!.stdin_data || '';
      }
    });
  }

  runCode() {
    this.isRunning = true;
    this.lastResult = null;
    
    // Using the synchronous endpoint for immediate feedback
    this.executionService.runCode({
      language: this.language,
      code: this.code,
      stdin: this.stdin,
      project_id: this.projectId || undefined
    }).subscribe({
      next: (res) => {
        if (res.success && res.data) {
          this.lastResult = res.data;
        }
        this.isRunning = false;
      },
      error: (err) => {
        this.isRunning = false;
        // Construct a fake result to show the error
        this.lastResult = {
          execution_id: 'error',
          status: 'FAILED',
          language: this.language,
          stdout: '',
          stderr: err.error?.detail || 'An unknown error occurred connecting to the execution engine.',
          exit_code: -1,
          execution_time: 0,
          memory_used_bytes: 0,
          created_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
        };
      }
    });
  }
}
