import numpy as np


def reciprocal_rank(recommended_list, bought_list, k=1):
    bought_list = np.array(bought_list)
    recommended_list = np.array(recommended_list)[:k]
    rank  = np.flatnonzero(np.isin(recommended_list, bought_list))
    if len(rank) == 0:
        rank = 0
    else:
        rank = 1 / (rank[0] + 1)
    return rank

def reciprocal_rank_mean(recommended_list_users, bought_list_users, k=3):
    rank_user = []
    for rec, bought in zip(recommended_list_users, bought_list_users):
        rank_user.append(reciprocal_rank(rec, bought, k=k))
    return  np.mean(rank_user)


if __name__ == '__main__':

    print(reciprocal_rank([2, 3, 4, 143, 132, 1134, 991, 27, 1543, 3345, 533, 11, 43], [521, 32, 143], k=3))