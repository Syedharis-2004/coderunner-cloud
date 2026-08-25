import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ResponseEnvelope } from './auth.service';

export interface ProjectSummary {
  id: string;
  name: string;
  language: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends ProjectSummary {
  description?: string;
  code: string;
  stdin_data?: string;
  public_share_id?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

@Injectable({
  providedIn: 'root'
})
export class ProjectService {
  private apiUrl = `${environment.apiUrl}/projects`;

  constructor(private http: HttpClient) {}

  getProjects(page: number = 1, size: number = 20, language?: string): Observable<ResponseEnvelope<PaginatedResponse<ProjectSummary>>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('size', size.toString());
    
    if (language) {
      params = params.set('language', language);
    }

    return this.http.get<ResponseEnvelope<PaginatedResponse<ProjectSummary>>>(this.apiUrl, { params });
  }

  getProject(id: string): Observable<ResponseEnvelope<ProjectDetail>> {
    return this.http.get<ResponseEnvelope<ProjectDetail>>(`${this.apiUrl}/${id}`);
  }

  getSharedProject(shareId: string): Observable<ResponseEnvelope<ProjectDetail>> {
    return this.http.get<ResponseEnvelope<ProjectDetail>>(`${this.apiUrl}/shared/${shareId}`);
  }

  createProject(data: any): Observable<ResponseEnvelope<ProjectDetail>> {
    return this.http.post<ResponseEnvelope<ProjectDetail>>(this.apiUrl, data);
  }

  updateProject(id: string, data: any): Observable<ResponseEnvelope<ProjectDetail>> {
    return this.http.patch<ResponseEnvelope<ProjectDetail>>(`${this.apiUrl}/${id}`, data);
  }

  deleteProject(id: string): Observable<ResponseEnvelope<any>> {
    return this.http.delete<ResponseEnvelope<any>>(`${this.apiUrl}/${id}`);
  }
}
