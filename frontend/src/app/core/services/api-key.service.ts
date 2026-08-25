import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ResponseEnvelope } from './auth.service';

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  revoked_at: string | null;
  created_at: string;
  raw_key?: string; // Only present on creation
}

@Injectable({
  providedIn: 'root'
})
export class ApiKeyService {
  private apiUrl = `${environment.apiUrl}/api-keys`;

  constructor(private http: HttpClient) {}

  listKeys(): Observable<ResponseEnvelope<ApiKey[]>> {
    return this.http.get<ResponseEnvelope<ApiKey[]>>(this.apiUrl);
  }

  createKey(name: string): Observable<ResponseEnvelope<ApiKey>> {
    return this.http.post<ResponseEnvelope<ApiKey>>(this.apiUrl, { name });
  }

  revokeKey(id: string): Observable<ResponseEnvelope<any>> {
    return this.http.delete<ResponseEnvelope<any>>(`${this.apiUrl}/${id}`);
  }
}
