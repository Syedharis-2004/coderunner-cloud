import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ResponseEnvelope } from './auth.service';

export interface UsageStats {
  billing_period: string;
  plan: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  api_executions: number;
  total_compute_seconds: number;
  monthly_limit: number;
  remaining: number;
  timeout_seconds: number;
  memory_limit: string;
}

@Injectable({
  providedIn: 'root'
})
export class UsageService {
  private apiUrl = `${environment.apiUrl}/usage`;

  constructor(private http: HttpClient) {}

  getCurrentUsage(): Observable<ResponseEnvelope<UsageStats>> {
    return this.http.get<ResponseEnvelope<UsageStats>>(`${this.apiUrl}/current`);
  }
}
