# Frontend forms

The Baserow frontend has a form pattern to create reusable and optionally nested form
components using the form mixin (`modules/core/mixins/form.js`). This pattern is a
consistent way of creating forms, validation, reusability, and error handling.

## Structure

- A form is always a standalone component that adds the `modules/core/mixins/form.js`
  mixin.
- The `allowedValues` data should be an array containing the fields that are included 
  in the form. Only these values will be included in the submit parameter.
- The `values` data should contain an object with the default values. This can be
  overwritten by setting the property `:default-values={}` on the component.
- A button should never submit a form directly. This must happen through the 
  `<form @submit>` event because that allows for native form submission like hitting the 
  enter key on an input.
- If Vuelidate `validations` are provided, then the form mixin automatically blocks
  submission if the form is not valid.
- The form values can be reset by calling `this.reset()`.

### Example form

```vue
<template>
  <form @submit.prevent="submit">
    <FormGroup
      small-label
      :label="$t('userForm.name')"
      required
      class="margin-bottom-2"
      :error="fieldHasErrors('name')"
    >
      <FormInput
        ref="name"
        v-model="values.name"
        size="large"
        :error="fieldHasErrors('name')"
        @blur="$v.values.name.$touch()"
      >
      </FormInput>
      <template #error>{{ $t('error.requiredField') }}</template>
    </FormGroup>

    <FormGroup
      small-label
      :label="$t('userForm.email')"
      required
      class="margin-bottom-2"
      :error="fieldHasErrors('email')"
    >
      <FormInput
        ref="email"
        v-model="values.email"
        size="large"
        :error="fieldHasErrors('email')"
        @blur="$v.values.email.$touch()"
      >
      </FormInput>
      <template #error>{{ $t('error.required') }}</template>
    </FormGroup>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'UserForm',
  mixins: [form],
  data() {
    return {
      allowedValues: ['name', 'email'],
      values: {
        name: '',
        email: '',
      },
    }
  },
  validations: {
    values: {
      name: { required },
      email: { required },
    },
  },
}
</script>
```

### Usage example

```vue
<template>
  <UserForm @submitted="submitted">
    <div class="actions">
      <Button type="primary" :disabled="loading" :loading="loading">
        {{ $t('action.create') }}</Button
      >
    </div>
  </UserForm>
</template>

<script>
export default {
  data() {
    return {
      loading: false,
    }  
  },
  methods: {
    submitted(values) {
      if (this.loading) {
          return
      }
      this.loading = true
      console.log(values)  // {'name': 'Bram', 'email': 'bram@example.com'}
    }
  }
}
</script>
```

## Reusability

The idea is that each form is a component that can be reused for different purposes,
think of using it to create a new object, or to update an existing one. If the form just
holds inputs, and no actions, then it can easily be reused.

In the previous example, the form is used to create an object, but the same form can
easily be reused to edit an existing object as well.

```vue
<template>
  <UserForm
      :default-values="{name: 'Bram', email: 'bram@example.com'}"
      @submitted="submitted"
  >
    <div class="actions">
      <Button type="primary" :disabled="loading" :loading="loading">
        {{ $t('action.update') }}</Button
      >
    </div>
  </UserForm>
</template>
...
```

## Nesting

In some case, you might want to have a dynamic child form, like what we do in Baserow 
when creating a new field in a table. Here we load a child form depending on the field
type that has been chosen in the dropdown 
(`modules/database/components/field/FieldForm.vue`).

The form mixin automatically recognizes if there is a child form, and will combine the
values when the form is submitted, so that the parent component listening to the root
form `@submitted` event receives a single object containing the values of the root and 
child forms. It can be nested multiple levels deep. The validation is automatically
checked in the children as well, and will also submit if all are valid.

```vue
<template>
  <form @submit.prevent="submit">
    <FormGroup
      small-label
      :label="$t('userForm.email')"
      required
      class="margin-bottom-2"
      :error="fieldHasErrors('email')"
    >
      <FormInput
        ref="email"
        v-model="values.email"
        size="large"
        :error="fieldHasErrors('email')"
        @blur="$v.values.email.$touch()"
      >
      </FormInput>
      <template #error>{{ $t('error.required') }}</template>
    </FormGroup>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'EmailForm',
  mixins: [form],
  data() {
    return {
      allowedValues: ['email'],
      values: {
        email: '',
      },
    }
  },
  validations: {
    values: {
      email: { required },
    },
  },
}
</script>
```

```vue
<template>
  <form @submit.prevent="submit">
    <FormGroup
      small-label
      :label="$t('userForm.name')"
      required
      class="margin-bottom-2"
      :error="fieldHasErrors('name')"
    >
      <FormInput
        ref="name"
        v-model="values.name"
        size="large"
        :error="fieldHasErrors('name')"
        @blur="$v.values.name.$touch()"
      >
      </FormInput>
      <template #error>{{ $t('error.requiredField') }}</template>
    </FormGroup>
    
    <EmailForm :default-values="defaultValues"></EmailForm>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'NameForm',
  mixins: [form],
  data() {
    return {
      allowedValues: ['name'],
      values: {
        name: '',
      },
    }
  },
  validations: {
    values: {
      name: { required },
    },
  },
}
</script>
```

```vue
<template>
  <UserForm @submitted="submitted">...</UserForm>
</template>

<script>
export default {
  methods: {
    submitted(values) {
      console.log(values)  // {'name': 'Bram', 'email': 'bram@example.com'}
    }
  }
}
</script>
```
