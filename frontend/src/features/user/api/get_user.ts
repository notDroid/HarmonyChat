import { getCurrentUserDetailsApiV1UsersMeGet } from '@/lib/api/user/user';
import { UserResponse } from '@/lib/api/model';

export default async function getCurrentUser() {
    const res = await getCurrentUserDetailsApiV1UsersMeGet();
    return res.data as UserResponse;
}