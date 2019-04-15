import { Component, OnInit, OnChanges } from '@angular/core';
import { Router } from '@angular/router';

@Component({
    selector: 'lumext-component',
    templateUrl: './lumext.component.html',
    host: { 'class': 'content-container' }
})
export class LumextComponent implements OnInit {

    constructor(private router: Router) { }

    ngOnInit() {
        const route = this.router.url.split(/\/lumext/)[0];
        const lumext = this.router.url.split(/\/lumext/)[1]
        console.log("route :", route, "lumext : ", lumext);
        if (!/\/user/.test(lumext) && !/\/group/.test(lumext)) {
            console.log("ici : ", route + '/lumext/user');
            this.router.navigateByUrl(route + '/lumext/user');
        }
    }
}