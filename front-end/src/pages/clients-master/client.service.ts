// client.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ClientWithContacts } from './client.model'; // Import the client model

@Injectable({
  providedIn: 'root',
})
export class ClientsService {
  private apiUrl =  '/api/intermediate-master/clients'; 

  constructor(private http: HttpClient) {}

  // Fetch all clients
  getClients(): Observable<ClientWithContacts[]> {
    return this.http.get<ClientWithContacts[]>(this.apiUrl);
  }

  // Fetch a client by ID
  getClientById(clientId: string): Observable<ClientWithContacts> {
    return this.http.get<ClientWithContacts>(`${this.apiUrl}/${clientId}`);
  }

  // Create a new client
  createClient(clients: ClientWithContacts): Observable<any> {
    return this.http.post(this.apiUrl, clients);
  }

  // Update a client
  updateClient(clientId: string, clients: ClientWithContacts): Observable<any> {
    return this.http.put(`${this.apiUrl}/${clientId}`, clients);
  }

  // Delete a client
  deleteClient(clientId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${clientId}`);
  }
}
