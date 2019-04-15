import { Component } from '@angular/core';

@Component({
  selector: 'group-component',
  templateUrl: './group.component.html',
  styleUrls: ['./group.component.css'],
  host: { 'class': 'content-container' },
})

export class GroupComponent {}
