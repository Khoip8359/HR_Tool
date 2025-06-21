<template>
    <div class="container-fluid py-4">
        <UserInfo></UserInfo>

        <div class="row">
            <!-- Left side - Subordinates Table -->
            <div class="col-lg-3 col-md-5 mb-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-primary text-white">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-people-fill me-2"></i>
                            Subordinates ({{ subordinatesCount }})
                        </h5>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th scope="col" class="border-0">
                                            <i class="bi bi-person me-1"></i>Employee
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr 
                                        v-for="(sub, index) in subordinates"
                                        :key="sub.sam_account || index"
                                        class="cursor-pointer"
                                        @click="selectEmployee(sub)"
                                        :class="{ 'table-active': selectedEmployee && selectedEmployee.sam_account === sub.sam_account }"
                                    >
                                        <td class="align-middle">
                                            <div class="d-flex align-items-center">
                                                <div class="avatar-circle me-3">
                                                    {{ getInitials(sub.display_name) }}
                                                </div>
                                                <div>
                                                    <h6 class="mb-1 fw-semibold">{{ sub.display_name }}</h6>
                                                    <small class="text-muted">
                                                        <i class="bi bi-envelope me-1"></i>{{ sub.mail || 'No email' }}
                                                    </small>
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        
                        <!-- Empty state -->
                        <div v-if="subordinatesCount === 0" class="text-center py-4">
                            <i class="bi bi-people text-muted" style="font-size: 3rem;"></i>
                            <p class="text-muted mt-2">No team members found</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right side - RouterView -->
            <div class="col-lg-9 col-md-7">
                <div class="card shadow-sm h-100">
                    <div class="card-body">
                        <!-- Truyền selectedEmployee xuống RouterView -->
                        <RouterView :selectedEmployee="selectedEmployee"></RouterView>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, provide, computed } from 'vue';
import UserInfo from '@/components/UserInfo.vue';
import { useUserStore } from '@/stores/user';

const selectedEmployee = ref(null);
const userStore = useUserStore();

// Provide selectedEmployee cho các component con có thể inject
provide('selectedEmployee', selectedEmployee);

// Computed properties để xử lý dữ liệu an toàn
const subordinates = computed(() => {
    return userStore?.user?.subordinates || [];
});

const subordinatesCount = computed(() => {
    return subordinates.value.length;
});

const selectEmployee = (employee) => {
    selectedEmployee.value = employee;
    console.log('Selected employee:', employee);
};

const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ')
        .map(word => word.charAt(0))
        .join('')
        .toUpperCase()
        .slice(0, 2);
};
</script>

<style scoped>
.cursor-pointer {
    cursor: pointer;
}

.avatar-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.875rem;
    flex-shrink: 0;
}

.table-hover tbody tr:hover {
    background-color: rgba(0, 123, 255, 0.05);
}

.table-active {
    background-color: rgba(0, 123, 255, 0.1) !important;
}

.card {
    border: none;
    border-radius: 12px;
}

.card-header {
    border-radius: 12px 12px 0 0 !important;
    border-bottom: none;
}

.badge {
    font-size: 0.75rem;
    padding: 0.375rem 0.75rem;
}

@media (max-width: 768px) {
    .col-lg-3 {
        margin-bottom: 1.5rem;
    }
}
</style>