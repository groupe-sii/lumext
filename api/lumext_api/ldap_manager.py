"""Manage LDAP objects
"""

import logging
import ldap
import ldap.modlist
import simplejson as json

from .utils import list_get, configuration_manager as cm

logger = logging.getLogger(__name__)


class LdapObject():
    """Define a simple LDAP object.
    """

    def __init__(self, base: str):
        """Create the object.

        Arg:
            base (str): LDAP Base path.
        """
        self.base = base
        if self.base:
            self.location = ",".join(base.split(',')[1:]) # Remove first information
        else:
            self.location = None

    def __repr__(self):
        """Represent the LdapUser object instance

        Returns:
            dict: Representation of object.
        """
        return f"{type(self)}({self.__dict__})"

    def get(self):
        """Get object as dict for JSON representation.

        Returns:
            dict: Dict representation of object.
        """
        return self.__dict__


class LdapUser(LdapObject):
    """Define a simple LDAP User
    """

    def __init__(self, base: str, login: list, display_name: list, description: list=[]):
        """Create a LDAP user.

        Args:
            base (str): LDAP Base path.
            login (list): userPrincipalName.
            display_name (list): A display name for the user.
            description (list, optional): Defaults to []. A description.
        """
        super().__init__(base)
        self.login = login
        self.display_name = display_name
        self.description = description

    def s_create(self, parent_ou, password):
        """Server side creation of User instance on LDAP server.
        """
        logger.debug(f"Creating user {self.login}...")
        self.base = f"CN={self.display_name},"
        self.base += "OU=Users," + get_ou_base(parent_ou)
        modlist = {
            "objectClass": [b'top', b'person', b'organizationalPerson', b'user'],
            "cn": [self.display_name.encode('utf-8')],
            "displayName": [self.display_name.encode('utf-8')],
            "samAccountName": [self.login.encode('utf-8')],
            "userPrincipalName": [f"{self.login}@{cm().ldap.domain}".encode('utf-8')],
            "userAccountControl": [f"{cm().ldap.userAccountControl}".encode('utf-8')],
            "unicodePwd": [f'"{password}"'.encode('utf-16-le')],
        }
        if self.description: # not mandatory
            modlist["description"] = [self.description.encode('utf-8')]

        con = get_ldap_connect()
        logger.trivia("Creation a user with following data: " + str(modlist))
        try:
            con.add_s(self.base, ldap.modlist.addModlist(modlist))
            logger.info(f"User {self.login} is created.")
        except Exception as e:
            logger.error(f"Cannot create user {self.login}: {str(e)}")
            return "500: Server side issue on creating user."
        return get_user_in_ou(parent_ou, self.login, as_dict=True)

    def s_edit(self, parent_ou, new_data: dict={}):
        """Server side edition of user's information on LDAP (only if modified)

        Args:
            new_data (dict): List of properties to change. Default is `{}`.
        """
        modlist = []
        if new_data.get('login'):
            modlist.append(get_modify_item('samAccountName', self.login, new_data.get('login')))
            modlist.append(get_modify_item('userPrincipalName',
                f"{self.login.decode('utf-8')}@{cm().ldap.domain}".encode('utf-8'),
                new_data.get('login') + f"@{cm().ldap.domain}"
            ))
        if new_data.get('description') is not None:
            if new_data.get('description') == "":
                # Empty description
                modlist.append((ldap.MOD_DELETE, 'description', None))
            else:
                modlist.append(get_modify_item('description', self.description, new_data.get('description')))
        if new_data.get('display_name'):
            modlist.append(get_modify_item('displayName', self.display_name, new_data.get('display_name')))
        if new_data.get('password'):
            # Reset password
            password = new_data.get('password')
            modlist.append(get_modify_item('unicodePwd',
                None, f'"{password}"', encoding="utf-16-le"
            ))
        modlist = list(filter(None.__ne__, modlist)) # remove empty changes
        logger.info(f"There is {len(modlist)} changes to make on the user object.")
        if len(modlist) > 0:
            logger.trivia(modlist)
            con = get_ldap_connect()
            try:
                con.modify_s(self.base, modlist)
                logger.info(f"User {self.login} is edited.")
            except Exception as e:
                logger.error(f"Cannot edit user {self.login}: {str(e)}")
                return "500: Server side issue on editing user."
        else:
            logger.debug("Nothing to edit.")
        return get_user_in_ou(parent_ou, new_data.get('login'), as_dict=True)

    def s_delete(self):
        """Server side deletion of User on LDAP Server
        """
        logger.debug(f"Deleting user {self.login}...")
        con = get_ldap_connect()
        try:
            con.delete_s(self.base)
            logger.info(f"User {self.login} is deleted.")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Cannot delete user {self.login}: {str(e)}")
            return "500: Server side issue on user deletion."


def get_ldap_connect():
    """Initialize a LDAP session.

    Returns:
        ldap.LDAPObject: new connection object for accessing the given LDAP server.
    """
    # Prepare connection settings (lazy connect)
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
    ldap.set_option(ldap.OPT_REFERRALS,0)
    ldap.protocol_version = 3
    # Add cacert file for LDAPs connections
    if "ldaps" in cm().ldap.address and cm().ldap.cacert_file:
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, cm().ldap.cacert_file)
    # Init connection
    con = ldap.initialize(
        cm().ldap.address,
        bytes_mode=False
    )
    # Bind user
    con.simple_bind_s(
        cm().ldap.user,
        cm().ldap.secret
    )
    return con


def ldap_search(base, filterstr="", attributes=[], scope: int=ldap.SCOPE_SUBTREE):
    """Run a LDAP search on directory.

    Args:
        base (str): LDAP Base to run query on.
        filterstr (str): A filter to apply on search.
        attributes (list): List of attrs to retrieves.
        scope (int, optional): default to `ldap.SCOPE_SUBTREE`. Scope for the LDAP request.

    Returns:
        list: A list of results.
    """
    logger.debug(f"Starting a new search on LDAP base: {base}.")
    logger.trivia(
        f"Parameters for the search are: filterstr: {filterstr} + attributes: {attributes} + scope: {scope}"
    )
    con = get_ldap_connect()
    try:
        return con.search_st(
            base,
            scope,
            filterstr,
            attributes,
            timeout=int(cm().ldap.search_timeout)
        )
    except ldap.TIMEOUT:
        logger.error(f"Exception raised while making query to the LDAP server: {str(e)}")
        return []
    except Exception as e:
        logger.warning(f"Exception raised while making query to the LDAP server: {str(e)}")
        return []


def get_ou_base(ou: str):
    """Return the full base of an OU

    Args:
        ou (str): OU to get the full path
    """
    return f"ou={ou},{cm().ldap.base}"


def get_modify_item(attribute, old_value, new_value, encoding="utf-8"):
    """Get modify modlist for an attribute.

    Args:
        attribute (str): Name of the attribute to change.
        old_value (str): Old value for this attribute.
        value (str): New value for this attribute.
        encoding (str, optional): Default to `utf-8`. Encoding to use
            for string conversion to bytes.
    """
    if old_value != new_value.encode('utf-8'):
        if attribute != 'unicodePwd': # no log for password
            logger.debug(f"Replacing value for attribute `{attribute}` from `{old_value}` to `{new_value}`")
        return (ldap.MOD_REPLACE, attribute, [new_value.encode(encoding)])
    else:
        return None


def test_tenant_for_ou(parent_ou: str):
    """Test if OU already exists in LDAP directory.

    If not: create it and its sub-OU.

    Args:
        parent_ou (str): Parent OU to lookup in directory.
    """
    logger.trivia(f"Testing if OU: {parent_ou} exists.")
    base = get_ou_base(parent_ou)
    filterstr = "(objectClass=organizationalUnit)"
    attributes = ['cn', 'name']
    # Look for tenant OU
    if not ldap_search(base, filterstr, attributes, scope=ldap.SCOPE_BASE):
        logger.debug(f"OU {parent_ou} not found. Creating...")
        create_ou(parent_ou, cm().ldap.base)
    else:
        logger.debug(f"OU {parent_ou} already exists")
    # Look for Users OU in tenant OU
    filterstr = "(&(objectClass=organizationalUnit)(name=Users))"
    if not ldap_search(base, filterstr, attributes, scope=ldap.SCOPE_ONELEVEL):
        logger.debug(f"OU {parent_ou}/Users not found. Creating...")
        create_ou("Users", base)
    else:
        logger.debug(f"OU {parent_ou}/Users already exists")
    # Look for Users OU in tenant OU
    filterstr = "(&(objectClass=organizationalUnit)(name=Groups))"
    if not ldap_search(base, filterstr, attributes, scope=ldap.SCOPE_ONELEVEL):
        logger.debug(f"OU {parent_ou}/Groups not found. Creating...")
        create_ou("Groups", base)
    else:
        logger.debug(f"OU {parent_ou}/Groups already exists")
    return


def create_ou(name, base):
    """Create an OU in LDAP directory.

    Args:
        name (str): Name of OU to create.
        base (str): Base path for OU creation.
    """
    logger.info(f"Creating OU {name}...")
    new_ou_base = f"OU={name}," + base
    modlist = {
        "objectClass": [b'top', b'organizationalUnit'],
        "cn": [name.encode('utf-8')],
        "name": [name.encode('utf-8')],
    }
    con = get_ldap_connect()
    logger.trivia("Creation of an OU with following data: " + str(modlist))
    try:
        con.add_s(new_ou_base, ldap.modlist.addModlist(modlist))
        logger.info(f"OU {name} is created.")
    except Exception as e:
        logger.error(f"Cannot create OU {name}: {str(e)}")
        return "500: Server side issue on creating OU."
    return


def list_users_in_ou(parent_ou: str, as_dict=False):
    """List the users from a specific OU

    Args:
        parent_ou (str): Parent OU to lookup in directory.
        as_dict (bool, optional): Defaults to False. Transform output to dict for JSON dumps.

    Returns:
        list: A list of LdapUser that belongs to the current OU.
    """
    logger.trivia(f"Listing users in OU: {parent_ou}")
    users = []
    # Test if parent OU(s) are existing
    test_tenant_for_ou(parent_ou)
    # Listing users
    base = get_ou_base(parent_ou)
    filterstr = "(objectClass=user)"
    attributes = ['displayName', 'description', 'userPrincipalName']
    for user in ldap_search(base, filterstr, attributes):
        # Each result tuple is of the form (dn, attrs)
        u = LdapUser(
            user[0],
            list_get(user[1].get('userPrincipalName'),0).split(b'@')[0],
            list_get(user[1].get('displayName'),0),
            list_get(user[1].get('description'),0)
        )
        if as_dict:
            u = u.get()
        users.append(u)
    logger.info(f"Found {len(users)} user(s) in OU {parent_ou}.")
    logger.trivia(users)
    return users


def get_user_in_ou(parent_ou: str, login: str, as_dict=False):
    """Get a specific user from a specific OU

    Args:
        parent_ou (str): Parent OU to lookup in directory.
        login (str): Login of the user to retrieve.
        as_dict (bool, optional): Defaults to False. Transform output to dict for JSON dumps.

    Returns:
        dict: A LdapUser that belongs to the current OU.
    """
    logger.trivia(f"Searching user with login {login} in OU: {parent_ou}")
    for user in list_users_in_ou(parent_ou):
        logger.trivia(f"Found a user with login {user.login.decode()}, comparing to the input...")
        if user.login.decode() == login:
            logger.info(f"Found user {login} in OU {parent_ou}.")
            if as_dict:
                user = user.get()
            return user
    logger.info(f"No user {login} found in OU {parent_ou}.")
    return None


def add_user_in_ou(parent_ou: str, data: dict):
    """Add a new user in OU

    Args:
        parent_ou (str): Parent OU where to create user.
        data (dict): Data for the new user creation.
    """
    # Test mandatory data
    for attr in ["login", "password", "display_name"]:
        if not data.get(attr):
            return f"400: Missing mandatory atttribute {attr} for user creation."
    if get_user_in_ou(parent_ou, data['login']):
        return f"400: User {data['login']} already exists."
    if data.get('password') != data.get('passwordConfirm'):
        return f"400: password and passwordConfirm mismatch."
    u = LdapUser(
        None, # empty base
        login = data.get('login'),
        display_name = data.get('display_name'),
        description = data.get('description')
    )
    return u.s_create(parent_ou, data.get('password'))


def edit_user_in_ou(parent_ou: str, login: str, new_data: dict):
    """Edit an existing user in an OU.

    Args:
        parent_ou (str): Parent OU to lookup in directory.
        login (str): Login of the user to retrieve.
        new_data (dict): Data for the new user to edit.

    Returns:
        dict: A LdapUser that belongs to the current OU.
    """
    u = get_user_in_ou(parent_ou, login)
    if not u:
        # Invalid user
        return None
    return u.s_edit(parent_ou, new_data)


def del_user_in_ou(parent_ou: str, login: str):
    """Delete an existing user in an OU.

    Args:
        parent_ou (str): Parent OU to lookup in directory.
        login (str): Login of the user to retrieve.

    Returns:
        bool: Does the operation succeed ?
    """
    u = get_user_in_ou(parent_ou, login)
    if not u:
        # Invalid user
        return None
    return u.s_delete()