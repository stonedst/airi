<script setup lang="ts">
import type { RemovableRef } from '@vueuse/core'

import {
  Alert,
  ProviderAdvancedSettings,
  ProviderBaseUrlInput,
  ProviderBasicSettings,
  ProviderSettingsContainer,
  ProviderSettingsLayout,
} from '@proj-airi/stage-ui/components'
import { useProvidersStore } from '@proj-airi/stage-ui/stores/providers'
import { FieldKeyValues } from '@proj-airi/ui'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()
const providersStore = useProvidersStore()
const { providers } = storeToRefs(providersStore) as { providers: RemovableRef<Record<string, any>> }
const loading = ref(0)

// Get provider metadata
const providerId = 'bilibili-danmaku'
const providerMetadata = computed(() => providersStore.getProviderMetadata(providerId))

const validationMessage = ref('')
const serviceTestResult = ref<{ success: boolean, message: string } | null>(null)
const isTestingService = ref(false)
const isConfiguringService = ref(false)
const configurationResult = ref<{ success: boolean, message: string } | null>(null)

// Base URL for the danmaku service
const baseUrl = computed({
  get: () => providers.value[providerId]?.baseUrl || providerMetadata.value?.defaultOptions?.().baseUrl || '',
  set: (value) => {
    if (!providers.value[providerId])
      providers.value[providerId] = {}

    providers.value[providerId].baseUrl = value
  },
})

// Bilibili API credentials
const ACCESS_KEY_ID = computed({
  get: () => providers.value[providerId]?.ACCESS_KEY_ID || '',
  set: (value) => {
    if (!providers.value[providerId])
      providers.value[providerId] = {}

    providers.value[providerId].ACCESS_KEY_ID = value
  },
})

const ACCESS_KEY_SECRET = computed({
  get: () => providers.value[providerId]?.ACCESS_KEY_SECRET || '',
  set: (value) => {
    if (!providers.value[providerId])
      providers.value[providerId] = {}

    providers.value[providerId].ACCESS_KEY_SECRET = value
  },
})

const APP_ID = computed({
  get: () => providers.value[providerId]?.APP_ID || '',
  set: (value) => {
    if (!providers.value[providerId])
      providers.value[providerId] = {}

    providers.value[providerId].APP_ID = value
  },
})

const ROOM_OWNER_AUTH_CODE = computed({
  get: () => providers.value[providerId]?.ROOM_OWNER_AUTH_CODE || '',
  set: (value) => {
    if (!providers.value[providerId])
      providers.value[providerId] = {}

    providers.value[providerId].ROOM_OWNER_AUTH_CODE = value
  },
})

const headers = ref(Object.entries(providers.value[providerId]?.headers ?? {}).map(([key, value]) => ({ key, value } as { key: string, value: string })) || [{ key: '', value: '' }])

function addKeyValue(headers: { key: string, value: string }[], key: string, value: string) {
  if (!headers)
    return

  headers.push({ key, value })
}

function removeKeyValue(index: number, headers: { key: string, value: string }[]) {
  if (!headers)
    return

  if (headers.length === 1) {
    headers[0].key = ''
    headers[0].value = ''
  }
  else {
    headers.splice(index, 1)
  }
}

// 测试服务是否可用
async function testService() {
  isTestingService.value = true
  serviceTestResult.value = null

  try {
    const baseUrlValue = baseUrl.value
    const response = await fetch(`${baseUrlValue}status`)

    if (!response.ok) {
      serviceTestResult.value = {
        success: false,
        message: t('settings.bilibili-danmaku.test.connectionFailed', {
          status: response.status,
          statusText: response.statusText,
        }),
      }
      return
    }

    const data = await response.json()
    if (data.running !== undefined) {
      serviceTestResult.value = {
        success: true,
        message: data.running
          ? t('settings.bilibili-danmaku.test.serviceRunning')
          : t('settings.bilibili-danmaku.test.serviceNotRunning'),
      }
    }
    else {
      serviceTestResult.value = {
        success: true,
        message: t('settings.bilibili-danmaku.test.serviceAvailable'),
      }
    }
  }
  catch (error) {
    serviceTestResult.value = {
      success: false,
      message: t('settings.bilibili-danmaku.test.connectionError', {
        error: error instanceof Error ? error.message : String(error),
      }),
    }
  }
  finally {
    isTestingService.value = false
  }
}

// 配置并启动服务
async function configureService() {
  isConfiguringService.value = true
  configurationResult.value = null

  try {
    const baseUrlValue = baseUrl.value
    const response = await fetch(`${baseUrlValue}configure`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ACCESS_KEY_ID: ACCESS_KEY_ID.value,
        ACCESS_KEY_SECRET: ACCESS_KEY_SECRET.value,
        APP_ID: APP_ID.value,
        ROOM_OWNER_AUTH_CODE: ROOM_OWNER_AUTH_CODE.value,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      configurationResult.value = {
        success: false,
        message: errorData.error
          ? t('settings.bilibili-danmaku.configure.configFailedWithError', { error: errorData.error })
          : t('settings.bilibili-danmaku.configure.configFailed', {
              status: response.status,
              statusText: response.statusText,
            }),
      }
      return
    }

    const data = await response.json()
    if (data.status === 'success') {
      configurationResult.value = {
        success: true,
        message: t('settings.bilibili-danmaku.configure.configSuccess'),
      }
    }
    else {
      configurationResult.value = {
        success: false,
        message: data.message
          ? t('settings.bilibili-danmaku.configure.configFailedWithMessage', { message: data.message })
          : t('settings.bilibili-danmaku.configure.configFailedGeneric'),
      }
    }
  }
  catch (error) {
    configurationResult.value = {
      success: false,
      message: t('settings.bilibili-danmaku.configure.configError', {
        error: error instanceof Error ? error.message : String(error),
      }),
    }
  }
  finally {
    isConfiguringService.value = false
  }
}

async function refetch() {
  loading.value++
  // service startup time
  const startValidationTimestamp = performance.now()
  let finalValidationMessage = ''

  try {
    const validationResult = await providerMetadata.value.validators.validateProviderConfig({
      baseUrl: baseUrl.value,
      ACCESS_KEY_ID: ACCESS_KEY_ID.value,
      ACCESS_KEY_SECRET: ACCESS_KEY_SECRET.value,
      APP_ID: APP_ID.value,
      ROOM_OWNER_AUTH_CODE: ROOM_OWNER_AUTH_CODE.value,
      headers: headers.value.filter(header => header.key !== '').reduce((acc, header) => {
        acc[header.key] = header.value
        return acc
      }, {} as Record<string, string>),
    })

    if (!validationResult.valid) {
      finalValidationMessage = t('settings.dialogs.onboarding.validationError', {
        error: validationResult.reason,
      })
    }
    else {
      finalValidationMessage = ''
    }
  }
  catch (error) {
    finalValidationMessage = t('settings.dialogs.onboarding.validationError', {
      error: error instanceof Error ? error.message : String(error),
    })
  }
  finally {
    setTimeout(() => {
      loading.value--
      validationMessage.value = finalValidationMessage
    }, 500 - (performance.now() - startValidationTimestamp))
  }
}

watch([baseUrl, ACCESS_KEY_ID, ACCESS_KEY_SECRET, APP_ID, ROOM_OWNER_AUTH_CODE, headers], refetch, { immediate: true })
watch(headers, refetch, { deep: true })

onMounted(() => {
  providersStore.initializeProvider(providerId)

  // Initialize refs with current values
  baseUrl.value = providers.value[providerId]?.baseUrl || providerMetadata.value?.defaultOptions?.().baseUrl || ''
  ACCESS_KEY_ID.value = providers.value[providerId]?.ACCESS_KEY_ID || ''
  ACCESS_KEY_SECRET.value = providers.value[providerId]?.ACCESS_KEY_SECRET || ''
  APP_ID.value = providers.value[providerId]?.APP_ID || ''
  ROOM_OWNER_AUTH_CODE.value = providers.value[providerId]?.ROOM_OWNER_AUTH_CODE || ''

  // Initialize headers if not already set
  if (!providers.value[providerId]?.headers) {
    providers.value[providerId].headers = {}
  }
  if (headers.value.length === 0) {
    headers.value = [{ key: '', value: '' }]
  }
})

function handleResetSettings() {
  providers.value[providerId] = {
    ...(providerMetadata.value?.defaultOptions as any),
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <Alert v-if="!!loading" type="loading">
      <template #title>
        {{ t('settings.pages.providers.provider.common.status.validating') }}
      </template>
    </Alert>
    <Alert v-else-if="!validationMessage" type="success">
      <template #title>
        {{ t('settings.pages.providers.provider.common.status.valid') }}
      </template>
    </Alert>
    <Alert v-else-if="validationMessage" type="error">
      <template #title>
        {{ t('settings.dialogs.onboarding.validationFailed') }}
      </template>
      <template v-if="validationMessage" #content>
        <div class="whitespace-pre-wrap break-all">
          {{ validationMessage }}
        </div>
      </template>
    </Alert>

    <!-- Service Test Result -->
    <Alert v-if="serviceTestResult && !isTestingService" :type="serviceTestResult.success ? 'success' : 'error'">
      <template #title>
        {{ serviceTestResult.success ? t('settings.bilibili-danmaku.test.success') : t('settings.bilibili-danmaku.test.failed') }}
      </template>
      <template #content>
        <div class="whitespace-pre-wrap break-all">
          {{ serviceTestResult.message }}
        </div>
      </template>
    </Alert>
    <Alert v-if="isTestingService" type="loading">
      <template #title>
        {{ t('settings.bilibili-danmaku.test.testing') }}
      </template>
    </Alert>

    <!-- Configuration Result -->
    <Alert v-if="configurationResult && !isConfiguringService" :type="configurationResult.success ? 'success' : 'error'">
      <template #title>
        {{ configurationResult.success ? t('settings.bilibili-danmaku.configure.success') : t('settings.bilibili-danmaku.configure.failed') }}
      </template>
      <template #content>
        <div class="whitespace-pre-wrap break-all">
          {{ configurationResult.message }}
        </div>
      </template>
    </Alert>
    <Alert v-if="isConfiguringService" type="loading">
      <template #title>
        {{ t('settings.bilibili-danmaku.configure.configuring') }}
      </template>
    </Alert>

    <ProviderSettingsLayout
      :provider-name="providerMetadata?.localizedName"
      :provider-icon="providerMetadata?.icon"
      :on-back="() => router.back()"
    >
      <ProviderSettingsContainer>
        <ProviderBasicSettings
          :title="t('settings.pages.providers.common.section.basic.title')"
          :description="t('settings.pages.providers.common.section.basic.description')"
          :on-reset="handleResetSettings"
        >
          <ProviderBaseUrlInput
            v-model="baseUrl"
            :placeholder="providerMetadata?.defaultOptions?.().baseUrl as string || ''"
            required
          />

          <div class="flex flex-col gap-2">
            <label class="flex flex-col gap-1">
              <span class="text-sm font-medium">
                {{ t('settings.bilibili-danmaku.fields.field.access_key_id.label') }}
              </span>
              <input
                v-model="ACCESS_KEY_ID"
                class="w-full border border-neutral-200 rounded-lg bg-neutral-50 px-3 py-2 text-sm outline-none dark:border-neutral-700 focus:border-primary-500 dark:bg-neutral-800 dark:focus:border-primary-500"
                type="password"
                :placeholder="t('settings.bilibili-danmaku.fields.field.access_key_id.placeholder')"
              >
            </label>

            <label class="flex flex-col gap-1">
              <span class="text-sm font-medium">
                {{ t('settings.bilibili-danmaku.fields.field.access_key_secret.label') }}
              </span>
              <input
                v-model="ACCESS_KEY_SECRET"
                class="w-full border border-neutral-200 rounded-lg bg-neutral-50 px-3 py-2 text-sm outline-none dark:border-neutral-700 focus:border-primary-500 dark:bg-neutral-800 dark:focus:border-primary-500"
                type="password"
                :placeholder="t('settings.bilibili-danmaku.fields.field.access_key_secret.placeholder')"
              >
            </label>

            <label class="flex flex-col gap-1">
              <span class="text-sm font-medium">
                {{ t('settings.bilibili-danmaku.fields.field.app_id.label') }}
              </span>
              <input
                v-model="APP_ID"
                class="w-full border border-neutral-200 rounded-lg bg-neutral-50 px-3 py-2 text-sm outline-none dark:border-neutral-700 focus:border-primary-500 dark:bg-neutral-800 dark:focus:border-primary-500"
                type="text"
                :placeholder="t('settings.bilibili-danmaku.fields.field.app_id.placeholder')"
              >
            </label>

            <label class="flex flex-col gap-1">
              <span class="text-sm font-medium">
                {{ t('settings.bilibili-danmaku.fields.field.room_owner_auth_code.label') }}
              </span>
              <input
                v-model="ROOM_OWNER_AUTH_CODE"
                class="w-full border border-neutral-200 rounded-lg bg-neutral-50 px-3 py-2 text-sm outline-none dark:border-neutral-700 focus:border-primary-500 dark:bg-neutral-800 dark:focus:border-primary-500"
                type="password"
                :placeholder="t('settings.bilibili-danmaku.fields.field.room_owner_auth_code.placeholder')"
              >
            </label>

            <!-- Test and Configure Service Buttons -->
            <div class="flex flex-wrap gap-2 pt-2">
              <button
                type="button"
                class="rounded-lg bg-primary-500 px-4 py-2 text-sm text-white font-medium dark:bg-primary-600 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 dark:hover:bg-primary-700 dark:focus:ring-offset-neutral-900"
                :disabled="isTestingService || isConfiguringService"
                @click="testService"
              >
                {{ t('settings.bilibili-danmaku.test.button') }}
              </button>

              <button
                type="button"
                class="rounded-lg bg-primary-500 px-4 py-2 text-sm text-white font-medium dark:bg-primary-600 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 dark:hover:bg-primary-700 dark:focus:ring-offset-neutral-900"

                :disabled="isTestingService || isConfiguringService"
                @click="configureService"
              >
                {{ t('settings.bilibili-danmaku.configure.button') }}
              </button>
            </div>
          </div>
        </ProviderBasicSettings>

        <ProviderAdvancedSettings :title="t('settings.pages.providers.common.section.advanced.title')">
          <FieldKeyValues
            v-model="headers"
            :label="t('settings.pages.providers.common.section.advanced.fields.field.headers.label')"
            :description="t('settings.pages.providers.common.section.advanced.fields.field.headers.description')"
            :key-placeholder="t('settings.pages.providers.common.section.advanced.fields.field.headers.key.placeholder')"
            :value-placeholder="t('settings.pages.providers.common.section.advanced.fields.field.headers.value.placeholder')"
            @add="(key: string, value: string) => addKeyValue(headers, key, value)"
            @remove="(index: number) => removeKeyValue(index, headers)"
          />
        </ProviderAdvancedSettings>
      </ProviderSettingsContainer>
    </ProviderSettingsLayout>
  </div>
</template>
