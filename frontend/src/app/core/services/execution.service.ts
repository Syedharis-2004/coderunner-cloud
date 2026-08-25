import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ResponseEnvelope } from './auth.service';
import { PaginatedResponse } from './project.service';

export interface ExecutionResult {
  execution_id: string;
  status: string;
  language: string;
  stdout: string;
  stderr: string;
  exit_code: number;
  execution_time: number;
  memory_used_bytes: number;
  created_at: string;
  completed_at: string;
}

export interface ExecutionQueueResponse {
  execution_id: string;
  status: string;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ExecutionService {
  private apiUrl = `${environment.apiUrl}/executions`;

  constructor(private http: HttpClient) {}

  getLanguages(): Observable<ResponseEnvelope<any[]>> {
    return this.http.get<ResponseEnvelope<any[]>>(`${this.apiUrl}/languages`);
  }

  runCode(payload: { language: string, code: string, stdin?: string, project_id?: string }): Observable<ResponseEnvelope<ExecutionResult>> {
    return this.http.post<ResponseEnvelope<ExecutionResult>>(`${this.apiUrl}/run`, payload);
  }

  queueCode(payload: { language: string, code: string, stdin?: string, project_id?: string }): Observable<ResponseEnvelope<ExecutionQueueResponse>> {
    return this.http.post<ResponseEnvelope<ExecutionQueueResponse>>(`${this.apiUrl}/queue`, payload);
  }

  getExecution(id: string): Observable<ResponseEnvelope<ExecutionResult>> {
    return this.http.get<ResponseEnvelope<ExecutionResult>>(`${this.apiUrl}/${id}`);
  }

  listExecutions(page: number = 1, size: number = 20, language?: string, status?: string): Observable<ResponseEnvelope<PaginatedResponse<ExecutionResult>>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('size', size.toString());
    
    if (language) params = params.set('language', language);
    if (status) params = params.set('status', status);

    return this.http.get<ResponseEnvelope<PaginatedResponse<ExecutionResult>>>(this.apiUrl, { params });
  }
}
