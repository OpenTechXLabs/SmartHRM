import { Component, OnInit, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

interface Contacts {
  co_name: string;
  co_position_hr: string;
  co_phno: string;
  co_email: string;
}

interface ClientsWithContacts {
  cl_id?: string;
  cl_name: string;
  cl_type: string;
  cl_email: string;
  cl_co_per_name: string;
  cl_addr: string;
  cl_map_url: string;
  cl_phno: string;
  cl_si_ag: boolean; // Checkbox for agreement signed
  cl_notes: string;
  contacts: Contacts[];
  formType?: 'add' | 'update' | 'view';
}

@Component({
  selector: 'app-clients-form',
  templateUrl: './client-form.component.html',
  styleUrls: ['./client-form.component.css'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatToolbarModule,
    MatCheckboxModule,
    MatCardModule,
    MatDialogModule,
    MatDividerModule,
  ],
})
export class ClientFormComponent implements OnInit {
  clients: ClientsWithContacts = {
    cl_name: '',
    cl_type: '',
    cl_email: '',
    cl_co_per_name: '',
    cl_addr: '',
    cl_map_url: '',
    cl_phno: '',
    cl_si_ag: false,
    cl_notes: '',
    contacts: [{ co_name: '', co_position_hr: '', co_phno: '', co_email: '' }],
    formType: 'add',
  };

  submitted: boolean = false; // Initialize as boolean
  formHeading: string = '';
  isSubmitDisabled: boolean = false;
  formInvalidMessage: string = ''; // Error message variable

  maxWords = 1000; // Word limit for client notes
  currentWordCount = 0; // Track current word count
  wordCountExceeded = false; // Track if word count is exceeded
maxLength: any;
  contact: any;
phoneInput: any;

  constructor(
    public dialogRef: MatDialogRef<ClientFormComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {}

  ngOnInit(): void {
    if (this.data && this.data.formType) {
      if (this.data.formType === 'add') {
        this.formHeading = 'Add New Client';
      } else if (this.data.formType === 'update') {
        this.formHeading = 'Edit Client';
        this.clients = {
          ...this.data,
          cl_si_ag: this.data.cl_ag_si === 1, // Convert 0/1 to boolean
        };
      } else if (this.data.formType === 'view') {
        this.formHeading = 'View Client';
        this.clients = {
          ...this.data,
          cl_si_ag: this.data.cl_ag_si === 1, // Convert 0/1 to boolean
        };
        this.isSubmitDisabled = true; // Disable submission for 'view' mode
      }
    }
  }

  closeDialog(): void {
    this.dialogRef.close();
  }

  onSubmit(): void {
    this.submitted = true;

    if (this.isValidForm()) {
      const dataToSend = {
        ...this.clients,
        cl_ag_si: this.clients.cl_si_ag ? 1 : 0, // Convert boolean to 1 or 0
      };

      if (this.clients.formType === 'add') {
        console.log('Client added:', dataToSend);
      } else if (this.clients.formType === 'update') {
        console.log('Client updated:', dataToSend);
      }

      this.dialogRef.close(dataToSend);
    }
  }

  isValidForm(): boolean {
    const isEmailValid = this.isValidEmail(this.clients.cl_email);
    const isPhoneValid = this.isValidPhone();

    const isFormValid =
      this.clients.cl_name !== '' &&
      this.clients.cl_email !== '' &&
      this.clients.cl_phno !== '' &&
      isEmailValid &&
      isPhoneValid &&
      !this.wordCountExceeded;

    if (!isFormValid) {
      this.formInvalidMessage = 'Please fill all mandatory fields correctly!';
    } else {
      this.formInvalidMessage = '';
    }

    return isFormValid;
  }

  isValidEmail(email: string): boolean {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailPattern.test(email);
  }

  isValidPhone(): boolean {
    const phoneRegex = /^\+?\d{1,4}[\s\-]?\(?\d{1,3}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}$/;
    return phoneRegex.test(this.clients.cl_phno);
  }

  isPhoneValid(phone: string): boolean {
    const phoneRegex = /^\+?\d{1,4}[\s\-]?\(?\d{1,3}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}$/;
    return phoneRegex.test(this.contact.co_phno);
  }
  

  checkWordCount(): void {
    const words = this.clients.cl_notes.trim().split(/\s+/);
    this.currentWordCount = words.length;

    this.wordCountExceeded = this.currentWordCount > this.maxWords;
    if (this.wordCountExceeded) {
      this.clients.cl_notes = this.clients.cl_notes.substring(
        0,
        this.clients.cl_notes.lastIndexOf(' ')
      );
    }
  }

  addContactPerson(): void {
    this.clients.contacts.push({
      co_name: '',
      co_position_hr: '',
      co_phno: '',
      co_email: '',
    });
  }

  removeContactPerson(index: number): void {
    if (this.clients.contacts.length > 1) {
      this.clients.contacts.splice(index, 1);
    }
  }
}
