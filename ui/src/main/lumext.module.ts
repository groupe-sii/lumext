import { LumextComponent } from './lumext.component';
import {CommonModule} from '@angular/common';
import {FormsModule, ReactiveFormsModule}  from '@angular/forms';
import {Inject, NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';
import {Store} from '@ngrx/store';
import {EXTENSION_ROUTE, ExtensionNavRegistration, ExtensionNavRegistrationAction} from '@vcd-ui/common';
import {UserComponent} from './business/user/user.component';
import {ROUTES} from './lumext.routes';

import {ClarityModule} from 'clarity-angular';
import { MenuComponent } from './business/menu.component/menu.component';
import { GroupComponent } from './business/group/group.component';

@NgModule({
    imports: [
        ClarityModule,
        CommonModule,
        RouterModule.forChild(ROUTES),
        FormsModule,
        ReactiveFormsModule
    ],
    declarations: [
        UserComponent,
        MenuComponent,
        LumextComponent,
        GroupComponent
    ],
    bootstrap: [
        UserComponent,
        LumextComponent
    ]
})
export class LumextModule {
    constructor(private appStore: Store<any>, @Inject(EXTENSION_ROUTE) extensionRoute: string) {
        const registration: ExtensionNavRegistration = {
            icon: '',
            path: extensionRoute,
            nameCode: 'nav.lumext',
            descriptionCode: 'nav.lumext.description'
        };
        appStore.dispatch(new ExtensionNavRegistrationAction(registration));
    }
}
