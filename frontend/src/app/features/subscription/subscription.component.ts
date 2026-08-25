import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { SubscriptionService, Subscription } from '../../core/services/subscription.service';
import { PaymentService, Payment } from '../../core/services/payment.service';

@Component({
  selector: 'app-subscription',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './subscription.component.html',
  styleUrls: ['./subscription.component.css']
})
export class SubscriptionComponent implements OnInit {
  subscription: Subscription | null = null;
  payments: Payment[] = [];
  loading = true;
  loadingPayments = true;
  processing = false;
  error: string | null = null;

  constructor(
    private subscriptionService: SubscriptionService,
    private paymentService: PaymentService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadSubscription();
    this.loadPaymentHistory();
  }

  loadSubscription() {
    this.loading = true;
    this.subscriptionService.getCurrentSubscription().subscribe({
      next: (response: any) => {
        if (response.success) {
          this.subscription = response.data || null;
        }
        this.loading = false;
      },
      error: (error: any) => {
        console.error('Failed to load subscription:', error);
        this.error = 'Failed to load subscription details.';
        this.loading = false;
      }
    });
  }

  loadPaymentHistory() {
    this.loadingPayments = true;
    this.paymentService.getPaymentHistory().subscribe({
      next: (response: any) => {
        if (response.success && response.data) {
          this.payments = response.data;
        }
        this.loadingPayments = false;
      },
      error: (error: any) => {
        console.error('Failed to load payment history:', error);
        this.loadingPayments = false;
      }
    });
  }

  openManageSubscription() {
    // SafePay does not have a hosted portal — redirect to subscription page
    this.router.navigate(['/subscription']);
  }

  cancelSubscription() {
    if (!confirm('Are you sure you want to cancel your subscription? You will retain access until the end of your billing period.')) {
      return;
    }

    this.processing = true;
    this.paymentService.cancelSubscription().subscribe({
      next: (response: any) => {
        if (response.success) {
          alert('Subscription canceled. You will retain access until ' +
            (this.subscription?.current_period_end ? new Date(this.subscription.current_period_end).toLocaleDateString() : 'the end of your billing period'));
          this.loadSubscription();
        }
        this.processing = false;
      },
      error: (error: any) => {
        console.error('Cancel error:', error);
        this.processing = false;
        alert(error.error?.detail || 'Failed to cancel subscription.');
      }
    });
  }

  reactivateSubscription() {
    this.processing = true;
    this.paymentService.reactivateSubscription().subscribe({
      next: (response: any) => {
        if (response.success) {
          alert('Subscription reactivated successfully!');
          this.loadSubscription();
        }
        this.processing = false;
      },
      error: (error: any) => {
        console.error('Reactivate error:', error);
        this.processing = false;
        alert(error.error?.detail || 'Failed to reactivate subscription.');
      }
    });
  }

  formatDate(dateString: string | null): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  formatAmount(amount: number, currency: string): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase()
    }).format(amount);
  }

  getStatusClass(status: string): string {
    const statusMap: {[key: string]: string} = {
      'active': 'status-active',
      'trialing': 'status-trialing',
      'past_due': 'status-warning',
      'canceled': 'status-canceled',
      'incomplete': 'status-warning'
    };
    return statusMap[status] || 'status-default';
  }

  getPaymentStatusClass(status: string): string {
    const statusMap: {[key: string]: string} = {
      'succeeded': 'payment-success',
      'pending': 'payment-pending',
      'failed': 'payment-failed'
    };
    return statusMap[status] || 'payment-default';
  }

  upgradePlan() {
    this.router.navigate(['/pricing']);
  }
}
