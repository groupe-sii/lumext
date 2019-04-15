import { Route } from '@angular/router';
import { UserComponent } from './business/user/user.component';
import { LumextComponent } from './lumext.component';
import { GroupComponent } from './business/group/group.component';

export const ROUTES: Route[] = [
    {
        path: '',
        component: LumextComponent,
        children: [
            { path: 'user', component: UserComponent },
            { path: 'group', component: GroupComponent },
            { path: '**', redirectTo: 'nasServer' }
        ]
    }
];
