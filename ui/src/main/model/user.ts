export class User {
  login: string;
  description: string;
  display_name: string;
  password: string;

  constructor(login: string, display_name: string, description: string, password: string) {
    this.login = login;
    this.display_name = display_name;
    this.description = description;
    this.password = password;
  }
}
