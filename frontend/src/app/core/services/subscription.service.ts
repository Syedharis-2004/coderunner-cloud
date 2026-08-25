import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Plan } from './plan.service';

export interface Subscription {
  id: string;
  user_id: string;
  plan_id: string;
  status: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  ended_at: string | null;
  trial_start: string | null;
  trial_end: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  allows_api_access: boolean;
  plan?: Plan;
}

export interface SubscriptionStatus {
  has_subscription: boolean;
  is_active: boolean;
  plan_name: string | null;
  plan_key: string | null;
  status: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  allows_api_access: boolean;
}

export interface ResponseEnvelope<T> {
  success: boolean;
  message?: string;
  data?: T;
}

@Injectable({
  providedIn: 'root'
})
export class SubscriptionService {
  private apiUrl = `${environment.apiUrl}/subscriptions`;

  constructor(private http: HttpClient) {}

  getCurrentSubscription(): Observable<ResponseEnvelope<Subscription | null>> {
    return this.http.get<ResponseEnvelope<Subscription | null>>(`${this.apiUrl}/current`);
  }

  getSubscriptionStatus(): Observable<ResponseEnvelope<SubscriptionStatus>> {
    return this.http.get<ResponseEnvelope<SubscriptionStatus>>(`${this.apiUrl}/status`);
  }

  cancelSubscription(cancelAtPeriodEnd: boolean = true, reason?: string): Observable<ResponseEnvelope<any>> {
    return this.http.post<ResponseEnvelope<any>>(`${this.apiUrl}/cancel`, {
      cancel_at_period_end: cancelAtPeriodEnd,
      reason: reason
    });
  }

  reactivateSubscription(): Observable<ResponseEnvelope<any>> {
    return this.http.post<ResponseEnvelope<any>>(`${this.apiUrl}/reactivate`, {});
  }
}
