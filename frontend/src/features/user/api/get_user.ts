import { 
  getCurrentUserDetailsApiV1UsersMeGet, 
  getUserDetailsByEmailApiV1UsersLookupGet, 
  getUserDetailsByIdApiV1UsersUserIdGet 
} from '@/lib/api/user/user';
import { UserResponse } from '@/lib/api/model';

export async function getCurrentUser() {
    const res = await getCurrentUserDetailsApiV1UsersMeGet();
    return res.data as UserResponse;
}

export async function getUserbyId(userId: string) {
    const res = await getUserDetailsByIdApiV1UsersUserIdGet(userId);
    const user = (res.data as UserResponse) || null;
    return user;
}

export async function getUserByEmail(email: string) {
    const res = await getUserDetailsByEmailApiV1UsersLookupGet({
        email: email
    });
    const user = (res.data as UserResponse) || null;
    return user;
}