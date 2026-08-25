import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;   // SafePay beacon/tracker token
}

export interface Payment {
  id: string;
  user_id: string;
  subscription_id: string | null;
  safepay_tracker: string | null;
  safepay_order_id: string | null;
  amount: number;
  currency: string;
  status: string;
  payment_type: string;
  description: string | null;
  failure_reason: string | null;
  receipt_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResponseEnvelope<T> {
  success: boolean;
  message?: string;
  data?: T;
}

@Injectable({ providedIn: 'root' })
export class PaymentService {
  private apiUrl = `${environment.apiUrl}/payments`;

  constructor(private http: HttpClient) {}

  /** Create a SafePay checkout session and get the redirect URL. */
  createCheckoutSession(
    planId: string,
    successUrl?: string,
    cancelUrl?: string,
  ): Observable<ResponseEnvelope<CheckoutSessionResponse>> {
    return this.http.post<ResponseEnvelope<CheckoutSessionResponse>>(
      `${this.apiUrl}/create-checkout-session`,
      { plan_id: planId, success_url: successUrl, cancel_url: cancelUrl },
    );
  }

  /**
   * Verify payment after SafePay redirects back.
   * Call this from the success page with query params.
   */
  verifyPayment(
    tracker: string,
    sig: string,
    ref?: string,
  ): Observable<ResponseEnvelope<{ status: string; plan: string }>> {
    const params: any = { tracker, sig };
    if (ref) params['ref'] = ref;
    return this.http.get<ResponseEnvelope<{ status: string; plan: string }>>(
      `${this.apiUrl}/verify`,
      { params },
    );
  }

  /** Cancel subscription at period end. */
  cancelSubscription(): Observable<ResponseEnvelope<{}>> {
    return this.http.post<ResponseEnvelope<{}>>(`${this.apiUrl}/cancel`, {});
  }

  /** Reactivate a subscription that was set to cancel. */
  reactivateSubscription(): Observable<ResponseEnvelope<{}>> {
    return this.http.post<ResponseEnvelope<{}>>(`${this.apiUrl}/reactivate`, {});
  }

  /** Get the user's payment history. */
  getPaymentHistory(): Observable<ResponseEnvelope<Payment[]>> {
    return this.http.get<ResponseEnvelope<Payment[]>>(`${this.apiUrl}/history`);
  }
}
