import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, Output, EventEmitter, Input } from '@angular/core';
import * as M from "materialize-css/dist/js/materialize";
import { NgForm } from '@angular/forms';
import { AWSClientService } from 'src/awsclient.service';
import { Template } from 'src/template';

@Component({
  selector: 'app-ec2',
  templateUrl: './ec2.component.html',
  styleUrls: ['./ec2.component.css']
})
export class Ec2Component implements OnInit, AfterViewInit {
  @Input() projectId: string;
  @Output() ec2Created: EventEmitter<any> = new EventEmitter();
  @ViewChild('instanceTypeSelect', {static:true}) instanceTypeSelect: ElementRef;
  @ViewChild('machineImageSelect', {static:true}) machineImageSelect: ElementRef;  

  private ec2Name: string = this.randomString();
  private ec2KeyPair: string = "OurEC2Keypair01";
  private instanceTypes: string[] = ["t2.micro"];
  private machineImages: string[] = ["ami-0e38b48473ea57778"];
  public isLoading: boolean;  

  randomString(length=10): string {
    let result = '';
    let characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    let charactersLength = characters.length;
    for (let i = 0; i < length; i++) {
       result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
  }

  constructor(private client: AWSClientService) { 
    this.isLoading = false;
  }

  ngOnInit() { }

  ngAfterViewInit() {
    M.FormSelect.init(this.instanceTypeSelect.nativeElement, {});    
    M.FormSelect.init(this.machineImageSelect.nativeElement, {});
    setTimeout(() => {
      M.updateTextFields();
    }, 100);
  }

  onSubmit(form: NgForm) {
    let {name, instanceType, keyName, machineImage} = form.value;   
    this.isLoading = true;
    setTimeout(() => {
      this.isLoading = false;
    }, 2000);
    this.ec2Created.emit({
      projectId: this.projectId,
      name,
      instanceType,
      machineImage,
      keyName,
      userData: "None", // TODO: get from UI
      state: "live" // TODO: get dynamic value
    });    
    let template = new Template();
    template.addEC2Instance(name, instanceType, keyName, machineImage);
    this.client.createStack(name+"EC2Instace", template).subscribe(value => {
      console.log("create stack repsonse: " + JSON.stringify(value));
    });
  }
}
