import { AfterViewInit } from '@angular/core';
import { Component } from '@angular/core';
import { Location } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'menu-component',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.css'],
})

export class MenuComponent {
  route: string;
  subVisible = true;

  constructor(location: Location, router: Router) {
    router.events.subscribe(() => {
      if (location.path() !== '') {
        this.route = location.path().split('/lumext/')[1];
      } else {
        this.route = 'home';
      }
    });
  }
  
}
