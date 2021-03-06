import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { AppRoutingModule, routingComponents } from './app-routing.module';
import { AppComponent } from './app.component';
import { Ec2Component } from './ec2/ec2.component';
import { CreateUserComponent } from './create-user/create-user.component';
import { AWSClientService, NotificationService, LoggingService } from 'src/services/services';
import { DynamodbComponent } from './dynamodb/dynamodb.component';

@NgModule({
  declarations: [
    AppComponent,
    routingComponents,
    Ec2Component,
    CreateUserComponent,
    DynamodbComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    ReactiveFormsModule,
    FormsModule,
  ],
  providers: [
    AWSClientService,
    NotificationService,
    LoggingService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
