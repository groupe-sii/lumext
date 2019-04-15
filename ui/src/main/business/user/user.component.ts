import { User } from './../../model/user';
import { LumextService } from './../../service/lumext.service';
import { Component, OnInit } from '@angular/core';
import { NgForm, FormGroup, FormControl, Validators, ValidatorFn, AbstractControl } from '@angular/forms';

@Component({
  selector: 'user-component',
  templateUrl: './user.component.html',
  styleUrls: ['./user.component.css'],
  host: { 'class': 'content-container' },
  providers: [LumextService]
})

export class UserComponent implements OnInit {
  users: User[];
  selectedUser: User;
  userdatagridloading: boolean = false;
  useraddmodal: boolean = false;
  userdetailsmodal: boolean = false;
  passwordmodal: boolean = false;
  useraddform = new FormGroup({
    login: new FormControl('', [Validators.required, Validators.pattern(/^[A-Za-z0-9\._-]{7,256}$/)]),
    display_name: new FormControl('', [Validators.required, Validators.maxLength(64), Validators.pattern(/^[\w+|\s]{5,64}$/)]),
    description: new FormControl('', Validators.maxLength(1024)),
    password: new FormControl('', [Validators.required, Validators.minLength(8), Validators.maxLength(127)]),
    passwordConfirm: new FormControl('', [this.validatorPassword()])
  });
  userdetailsform = new FormGroup({
    login: new FormControl(this.selectedUser ? this.selectedUser.login : '', [Validators.required, Validators.pattern(/^[A-Za-z0-9\._-]{7,256}$/)]),
    display_name: new FormControl(this.selectedUser ? this.selectedUser.display_name : '', [Validators.required, Validators.maxLength(64), Validators.pattern(/^[\w+|\s]{5,64}$/)]),
    description: new FormControl(this.selectedUser ? this.selectedUser.description : '', Validators.maxLength(1024)),
  });
  passwordform = new FormGroup({
    password: new FormControl('', [Validators.required, Validators.minLength(8), Validators.maxLength(127)]),
    passwordConfirm: new FormControl('', [this.validatorPasswordTwo()])
  });
  regexPassword: RegExp = /[\w+|\W]{8,127}/;
  passwordGenerated: string;
  visiblePassword = false;

  constructor(private lumextService: LumextService) { }

  ngOnInit(): void {
    this.getUsers();
  }

  openUserModal() {
    this.useraddmodal = true;
    this.useraddform.reset();
  }

  validatorPassword(): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } | null => {
      let forbidden = false;
      if (this.useraddform && this.regexPassword.test(this.useraddform.get('password').value) && this.useraddform.get('password').value === this.useraddform.get('passwordConfirm').value) {
        forbidden = true
      }
      return forbidden ? null : { 'forbidden': { value: control.value } };
    };
  }

  validatorPasswordTwo(): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } | null => {
      let forbidden = false;
      if (this.passwordform && this.regexPassword.test(this.passwordform.get('password').value) && this.passwordform.get('password').value === this.passwordform.get('passwordConfirm').value) {
        forbidden = true
      }
      return forbidden ? null : { 'forbidden': { value: control.value } };
    };
  }

  testConfirmPassword() {
    this.useraddform.get('passwordConfirm').updateValueAndValidity();
  }

  passwordGenerator(form: FormGroup) {
    let password = [];
    let passwordString = '';
    const minLength = 8;
    const maxLength = 15;
    const length = Math.floor(Math.random() * (maxLength - minLength)) + minLength;
    const character = []
    for (let i = 33; i < 127; i++) {
      let a = String.fromCharCode(i);
      character.push(a);
    }
    do {
      password = [];
      passwordString = ''
      for (let i = length + 1; i > 0; i--) {
        password.push(character[Math.floor(Math.random() * character.length)])
      }
      passwordString = password.join('');
    } while (!(/\W/).test(passwordString) && (/[a-z]/).test(passwordString) && (/[A-Z]/).test(passwordString) && (/\d/).test(passwordString))
    form.get('password').patchValue(passwordString);
    this.visiblePassword = true;
  }

  getUsers(): void {
    this.userdatagridloading = true;
    this.lumextService.getUsers().subscribe(users => {
      this.users = users;
      this.userdatagridloading = false;
    }, (err) => {
      this.userdatagridloading = false;
    });
    this.selectedUser = null;
  }

  createUserSubmit() {
    if (this.useraddform.valid) {
      this.userdatagridloading = true;
      this.useraddmodal = false;
      this.lumextService.addUser(JSON.stringify(this.useraddform.value)).subscribe(res => {
        this.useraddform.reset();
        this.userdatagridloading = false;
        this.getUsers();
      }, (err) => {
        this.getUsers();
        this.userdatagridloading = false;
      });
    }
  }

  createUserCancel(form: NgForm) {
    this.useraddmodal = false;
    form.reset();
  }

  userDetailsSubmit() {
    if (this.userdetailsform.valid) {
      this.userdatagridloading = true;
      this.userdetailsmodal = false;
      this.lumextService.editUser(this.selectedUser.login, this.userdetailsform.value).subscribe(newuser => {
        this.getUsers();
        this.userdetailsform.reset();
        this.userdatagridloading = false;
      }, (err) => {
        this.getUsers();
        this.userdatagridloading = false;
      });
    }
  }

  userDetailsCancel(form: NgForm) {
    this.userdetailsmodal = false;
    form.reset();
  }

  changePasswordSubmit() {
    if (this.passwordform.valid) {
      this.userdatagridloading = true;
      this.passwordmodal = false;
      this.lumextService.editUser(this.selectedUser.login, this.passwordform.value).subscribe(newuser => {
        this.getUsers();
      }, (err) => {
        this.getUsers();
      });
      this.userdatagridloading = false;
      this.passwordform.reset();
    }
  }

  userPasswordCancel(form: NgForm) {
    this.passwordmodal = false;
    form.reset();
  }

  deleteUser() {
    this.userdatagridloading = true;
    this.lumextService.deleteUser(this.selectedUser.login).subscribe(res => {
      this.getUsers();
      this.userdatagridloading = false;
    }, (err) => {
      this.getUsers();
      this.userdatagridloading = false;
    });
    this.selectedUser = null;
  }

  isInvalid(form: FormGroup, control: string): boolean {
    if(form && form.controls[control]) {
      return form.controls[control].invalid && form.controls[control].touched
    }
    return false;
  }
}
