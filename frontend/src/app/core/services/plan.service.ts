import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Plan {
  id: string;
  key: string;
  name: string;
  description: string | null;
  price_monthly: number | string;   // API returns string e.g. "9.00"
  monthly_executions: number;
  max_api_keys: number;
  timeout_seconds: number;
  api_access_enabled: boolean;
  priority_execution: boolean;
  support_level: string;
}

export interface ResponseEnvelope<T> {
  success: boolean;
  message?: string;
  data?: T;
}

@Injectable({
  providedIn: 'root'
})
export class PlanService {
  private apiUrl = `${environment.apiUrl}/plans`;

  constructor(private http: HttpClient) {}

  listPlans(): Observable<ResponseEnvelope<Plan[]>> {
    return this.http.get<ResponseEnvelope<Plan[]>>(this.apiUrl);
  }

  getPlan(planId: string): Observable<ResponseEnvelope<Plan>> {
    return this.http.get<ResponseEnvelope<Plan>>(`${this.apiUrl}/${planId}`);
  }

  getPlanByKey(planKey: string): Observable<ResponseEnvelope<Plan>> {
    return this.http.get<ResponseEnvelope<Plan>>(`${this.apiUrl}/key/${planKey}`);
  }
}
